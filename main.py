import asyncio
import os
import sys
import threading
from contextlib import asynccontextmanager
from typing import List, Dict, Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader
import docx

from src.spooler.task_list import TaskList
from src.devices.printer import Printer
from src.models.task import Task
from src.users.user import User

# Directory to store uploaded files
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

    yield  # server běží

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

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)
manager = ConnectionManager()
task_list = TaskList()
app = FastAPI(title="Print Spooler API", lifespan=lifespan)
STATIC_DIR = resource_path("static")
INDEX_FILE = os.path.join(STATIC_DIR, "index.html")
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
            "user": task.user.username
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
                "user": task.user.username
            } for task in queue_tasks
        ]
    }


def get_page_count(file_stream, filename: str) -> int:
    """
    Returns the number of pages in a file based on its type.

    Supports PDF, DOCX and common image formats (JPG, PNG).
    Defaults to 1 if page count cannot be determined.

    :param file_stream: file-like object
    :param filename: Name of the file
    :return: Number of pages in the file
    """
    filename = filename.lower()

    try:
        if filename.endswith('.pdf'):
            reader = PdfReader(file_stream)
            return len(reader.pages)

        elif filename.endswith('.docx'):
            document = docx.Document(file_stream)
            props = document.core_properties
            if props.pages and props.pages > 0:
                return props.pages
            else:
                print("Warning: DOCX page count metadata missing, defaulting to 1.")
                return 1

        elif filename.endswith(('.jpg', '.jpeg', '.png')):
            return 1

        else:
            return 1

    except Exception as e:
        print(f"Error reading file {filename}: {e}. Defaulting to 1 page.")
        return 1


@app.post("/tasks/")
async def create_task(username: str = Form(...), priority: int = Form(...), file: UploadFile = File(...)):
    """
    Creates a new print task and adds it to the queue.

    :param username: Name of the user submitting the task
    :param priority: Task priority
    :param file: Uploaded file
    :return: JSON message with task status
    """

    try:
        # Save the uploaded file
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        # Handle duplicate filenames
        base_name, extension = os.path.splitext(file.filename)
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(UPLOAD_DIR, f"{base_name}_{counter}{extension}")
            counter += 1

        # Write file to disk
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Reset file pointer for page counting
        file.file.seek(0)
        pages = get_page_count(file.file, file.filename)
        print(f"Pages counted: {pages}")

        user_obj = User(username=username, task_list=task_list, number_of_tasks=0)

        new_task = Task(
            name=file.filename,
            pages=pages,
            priority=priority,
            user=user_obj,
            file_path=file_path  # Add file path to task
        )

        task_list.append(new_task)

        await manager.broadcast(f"NEW: New task added {new_task.name} by {user_obj.username}")
        state = await get_system_state()
        await manager.broadcast_json({"type": "system_state", "data": state})

        return {"message": "Task successfully added.", "task_id": new_task.name}

    except Exception as e:
        return {"error": f"Error adding task: {e}"}


@app.get("/system-state/")
async def system_state_endpoint():
    """
    Returns the current system state as JSON.

    :return: Dictionary with printer status and task queue
    """
    return await get_system_state()


@app.get("/")
async def get_root():
    """
    Serves the main frontend HTML page.

    :return: FileResponse with index.html
    """
    return FileResponse(INDEX_FILE)


@app.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time system updates.

    :param websocket: WebSocket connection to client
    :return:
    """
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