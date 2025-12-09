import asyncio
import os
import sys
import threading
import json
import secrets
from contextlib import asynccontextmanager
from datetime import timedelta, datetime
from typing import List, Dict, Any, Optional

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form, Request, Depends, HTTPException, status
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pypdf import PdfReader

from src.spooler.task_list import TaskList
from src.devices.printer import Printer
from src.models.task import Task

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

USERS_FILE = "src/user/users.json"
SESSIONS_FILE = "src/user/sessions.json"
SESSION_DURATION = timedelta(hours=24)


def load_users() -> Dict[str, str]:
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": "admin123"
        }
        with open(USERS_FILE, 'w') as f:
            json.dump(default_users, f, indent=2)
        print(f"Created {USERS_FILE} with default admin user")
        return default_users

    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def load_sessions() -> Dict[str, Dict[str, Any]]:
    if not os.path.exists(SESSIONS_FILE):
        return {}
    try:
        with open(SESSIONS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_sessions(sessions: Dict[str, Dict[str, Any]]):
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f, indent=2)


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    sessions = load_sessions()
    sessions[token] = {
        "username": username,
        "created": datetime.now().isoformat(),
        "expires": (datetime.now() + SESSION_DURATION).isoformat()
    }
    save_sessions(sessions)
    return token


def get_current_user(request: Request) -> Optional[str]:
    token = request.cookies.get("session_token")
    if not token:
        return None

    sessions = load_sessions()
    session = sessions.get(token)

    if not session:
        return None

    expires = datetime.fromisoformat(session["expires"])
    if datetime.now() > expires:
        del sessions[token]
        save_sessions(sessions)
        return None

    return session["username"]


async def require_auth(request: Request):
    """Dependency to require authentication."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    return user
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

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)
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
        else:
            return 1

    except Exception as e:
        print(f"Error reading file {filename}: {e}. Defaulting to 1 page.")
        return 1

@app.post("/api/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    users = load_users()

    if username not in users or users[username] != password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    token = create_session(username)

    response = JSONResponse(content={"message": "Login successful"})
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        max_age=int(SESSION_DURATION.total_seconds()),
        samesite="lax"
    )

    return response


@app.post("/api/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    if token:
        sessions = load_sessions()
        if token in sessions:
            del sessions[token]
            save_sessions(sessions)

    response = JSONResponse(content={"message": "Logged out"})
    response.delete_cookie("session_token")
    return response

@app.get("/api/check-auth")
async def check_auth(request: Request):
    user = get_current_user(request)
    if user:
        return {"authenticated": True, "username": user}
    return {"authenticated": False}


@app.post("/tasks/")
async def create_task(request: Request,username: str = Form(...),priority: int = Form(...),file: UploadFile = File(...),current_user: str = Depends(require_auth)):
    """
    Creates a new print task and adds it to the queue.
    """
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)

        base_name, extension = os.path.splitext(file.filename)
        counter = 1
        while os.path.exists(file_path):
            file_path = os.path.join(UPLOAD_DIR, f"{base_name}_{counter}{extension}")
            counter += 1

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        file.file.seek(0)
        pages = get_page_count(file.file, file.filename)
        print(f"Pages counted: {pages}")

        new_task = Task(
            name=file.filename,
            pages=pages,
            priority=priority,
            username=username,
            file_path=file_path
        )

        task_list.append(new_task)

        await manager.broadcast(f"NEW: New task added {new_task.name} by {new_task.username}")
        state = await get_system_state()
        await manager.broadcast_json({"type": "system_state", "data": state})

        return {"message": "Task successfully added.", "task_id": new_task.name}

    except Exception as e:
        return {"error": f"Error adding task: {e}"}



@app.get("/system-state/")
async def system_state_endpoint(request: Request, current_user: str = Depends(require_auth)):
    """
    Returns the current system state as JSON.

    :return: Dictionary with printer status and task queue
    """
    return await get_system_state()

@app.get("/login")
async def get_login():
    """
    Serves the login page.
    """
    return FileResponse(LOGIN_FILE)

@app.get("/")
async def get_root(request: Request):
    """
    Serves the main frontend HTML page.

    :return: FileResponse with index.html
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return FileResponse(INDEX_FILE)


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
