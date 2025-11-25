import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any

from src.spooler.task_list import TaskList
from src.devices.printer import Printer
from src.models.task import Task
from src.users.user import User
import threading

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.lock = threading.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        with self.lock:
            self.active_connections.append(websocket)
        await websocket.send_text("INFO: Successfully connected to server")

    def disconnect(self, websocket: WebSocket):
        with self.lock:
            self.active_connections.remove(websocket)

    async def broadcast_json(self, data: Dict[str, Any]):
        for connection in self.active_connections:
            await connection.send_json(data)

    async def broadcast(self, message: str):
        print("Broadcast: " + message)
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()
task_list = TaskList()
app = FastAPI(title="Print Spooler API")

class TaskRequest(BaseModel):
    name: str
    pages: int
    priority: int
    username: str

async def get_system_state():
    """Standalone function to get system state"""
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
        "current_task": current_task_dict,
        "queue_length": queue_length,
        "queue_tasks": [
            {
                "name": task.name,
                "pages": task.pages,
                "priority": task.priority,
                "user": task.user.username
            }
            for task in queue_tasks
        ]
    }

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()

    printer = Printer(
        task_list=task_list,
        manager=manager,
        loop=loop,
        name="MainPrinter",
        get_system_state_func=get_system_state
    )
    printer.start()

    app.state.printer = printer
    print("Server started, printer runs")

@app.on_event("shutdown")
async def shutdown_event():
    print("Server is stopping")
    app.state.printer.stop()

@app.post("/tasks/")
async def create_task(task_req: TaskRequest):
    try:
        user_obj = User(username=task_req.username, task_list=task_list, number_of_tasks=0)

        new_task = Task(
            name=task_req.name,
            pages=task_req.pages,
            priority=task_req.priority,
            user=user_obj
        )

        task_list.append(new_task)

        await manager.broadcast(f"NEW: New task added {new_task.name} by {user_obj.username}")

        state = await get_system_state()
        await manager.broadcast_json({"type": "system_state", "data": state})

        return {"message": "Task successfully added.", "task_id": new_task.name}
    except Exception as e:
        return {"error": f"Error adding task: {e}"}

@app.get("/tasks/")
async def get_tasks():
    queue_length, queue_details = task_list.get_queue_info()
    return {
        "current_queue_length": queue_length,
        "queue_details": queue_details
    }

@app.delete("/tasks/")
async def clear_tasks():
    """Clear all tasks from queue"""
    task_list.clear()

    state = await get_system_state()
    await manager.broadcast_json({"type": "system_state", "data": state})
    return {"message": "All tasks cleared"}

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/system-state/")
async def system_state_endpoint():
    """Endpoint to get current system state"""
    return await get_system_state()

@app.get("/")
async def get_root():
    return FileResponse("static/index.html")

@app.websocket("/ws/status")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print(f"Client {websocket.client} disconnected.")