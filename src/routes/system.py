from fastapi import APIRouter, Request, Depends
from src.auth.session_manager import require_auth

router = APIRouter(prefix="/system-state", tags=["system"])

get_system_state_func = None

def initialize_system_router(state_func):
    global get_system_state_func
    get_system_state_func = state_func

@router.get("/")
async def get_system_state(request: Request, current_user: str = Depends(require_auth)):
    return await get_system_state_func()