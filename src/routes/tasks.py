import os
from fastapi import APIRouter, Request, UploadFile, File, Form, Depends
from pypdf import PdfReader

from src.auth.session_manager import require_auth
from src.spooler.task_list import TaskList
from src.models.task import Task

router = APIRouter(prefix="/tasks", tags=["tasks"])

task_list: TaskList = None
manager = None
get_system_state_func = None
UPLOAD_DIR = "uploaded_files"

def initialize_task_router(tl: TaskList, conn_manager, state_func, upload_dir: str):
    global task_list, manager, get_system_state_func, UPLOAD_DIR
    task_list = tl
    manager = conn_manager
    get_system_state_func = state_func
    UPLOAD_DIR = upload_dir

def get_page_count(file_stream, filename: str) -> int:
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

@router.post("/")
async def create_task(request: Request,username: str = Form(...),priority: int = Form(...),file: UploadFile = File(...),current_user: str = Depends(require_auth)):
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
        state = await get_system_state_func()
        await manager.broadcast_json({"type": "system_state", "data": state})

        return {"message": "Task successfully added.", "task_id": new_task.name}

    except Exception as e:
        return {"error": f"Error adding task: {e}"}