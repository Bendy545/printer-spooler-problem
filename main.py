import asyncio
import os
import sys
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Dict, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.staticfiles import StaticFiles
from src.spooler.task_list import TaskList
from src.devices.printer import Printer
from src.routes import auth, system, tasks, pages
from src.auth.session_manager import load_sessions

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ConnectionManager:
    def __init__(self):
        """
        This class manages active WebSocket connections to facilitate real-time broadcasting.

        active_connections: list of currently open connections.
        lock: ensures thread-safe access to the active_connections list.
        """
        self.active_connections: List[WebSocket] = []
        self.lock = threading.Lock()

    async def connect(self, websocket: WebSocket):
        """
        Accepts a new WebSocket connection and adds it to the active_connections list.

        :param websocket: WebSocket object representing the client connection.
        """
        await websocket.accept()
        with self.lock:
            self.active_connections.append(websocket)
        await websocket.send_text("INFO: Successfully connected to server")

    def disconnect(self, websocket: WebSocket):
        """
        Removes a WebSocket connection from the active_connections list.

        :param websocket: WebSocket object representing the client connection.
        """
        with self.lock:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, data: Dict[str, Any]):
        """
        Broadcasts a JSON message to all active websocket connections.

        :param data: Dictionary to be sent as JSON
        """
        for connection in self.active_connections:
            await connection.send_json(data)

    async def broadcast(self, message: str):
        """
        Broadcasts a plain text message to all active WebSocket connections.

        :param message: The message string to broadcast
        """
        print("Broadcast: " + message)
        for connection in self.active_connections:
            await connection.send_text(message)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan handler for FastAPI.
    Starts printer on server startup and stops it on shutdown.
    """
    print("Server starting...")

    loop = asyncio.get_event_loop()

    printer = Printer(
        task_list=task_list,
        manager=manager,
        loop=loop,
        name="MainPrinter",
        get_system_state_func=get_system_state,
        printer_name="Xprinter"
    )
    printer.start()
    app.state.printer = printer

    yield

    print("Server stopping...")
    app.state.printer.stop()


def resource_path(relative_path):
    """
    Resolves file path for runtime and PyInstaller app.

    :param relative_path: Relative path to file
    :return: Absolute path to file
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)

    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

manager = ConnectionManager()
task_list = TaskList()
app = FastAPI(title="Print Spooler API", lifespan=lifespan)
STATIC_DIR = resource_path("static")
INDEX_FILE = os.path.join(STATIC_DIR, "index.html")
LOGIN_FILE = os.path.join(STATIC_DIR, "login.html")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


async def get_system_state():
    """
    Returns current system state including printer status and task queue.

    :return: Dictionary containing printer status, current task, queue length, and task list
    """
    queue_tasks = task_list.get_all_tasks()
    queue_length = len(task_list)
    printer_status = app.state.printer.get_status()
    current_task_dict = None
    if printer_status['current_task']:
        task = printer_status['current_task']
        current_task_dict = {
            "name": task.name,
            "pages": task.pages,
            "priority": task.priority,
            "user": task.username
        }
    return {
        "printer_status": "printing" if printer_status['is_printing'] else "idle",
        "printer_available": printer_status.get('printer_available', False),
        "current_task": current_task_dict,
        "queue_length": queue_length,
        "queue_tasks": [
            {
                "name": task.name,
                "pages": task.pages,
                "priority": task.priority,
                "user": task.username
            } for task in queue_tasks
        ]
    }

tasks.initialize_task_router(task_list, manager, get_system_state, UPLOAD_DIR)
system.initialize_system_router(get_system_state)
pages.initialize_page_router(INDEX_FILE, LOGIN_FILE)

app.include_router(auth.router)
app.include_router(system.router)
app.include_router(pages.router)
app.include_router(tasks.router)

@app.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time system updates.

    :param websocket: WebSocket connection to client
    :return:
    """
    cookies = websocket.cookies
    token = cookies.get("session_token")

    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    sessions = load_sessions()
    session = sessions.get(token)

    if not session:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    expires = datetime.fromisoformat(session["expires"])
    if datetime.now() > expires:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client {websocket.client} disconnected.")

if __name__ == "__main__":
    import socket

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    print(f"Server starting on:")
    print(f"  - Local: http://127.0.0.1:8000")
    print(f"  - Network: http://{local_ip}:8000")
    print(f"\nOther devices on your network can access it at: http://{local_ip}:8000")

    uvicorn.run(app, host="0.0.0.0", port=8000)
