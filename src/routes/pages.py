from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, RedirectResponse
from src.auth.session_manager import get_current_user

router = APIRouter(tags=["pages"])

INDEX_FILE = None
LOGIN_FILE = None

def initialize_page_router(index_file: str, login_file: str):
    global INDEX_FILE, LOGIN_FILE
    INDEX_FILE = index_file
    LOGIN_FILE = login_file

@router.get("/")
async def get_root(request: Request):
    """
    Serves the main frontend HTML page.

    :return: FileResponse with index.html
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login")
    return FileResponse(INDEX_FILE)

@router.get("/login")
async def get_login():
    """
    Serves the login page.
    """
    return FileResponse(LOGIN_FILE)