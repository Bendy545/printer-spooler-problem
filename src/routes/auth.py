from fastapi import APIRouter, Request, Form, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import timedelta
from src.auth.session_manager import load_users, create_session, get_current_user, save_sessions, load_sessions, SESSION_DURATION

router = APIRouter(prefix="/api", tags=["authentication"])

@router.post("/login")
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

@router.post("/logout")
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

@router.get("/check-auth")
async def check_auth(request: Request):
    user = get_current_user(request)
    if user:
        return {"authenticated": True, "username": user}
    return {"authenticated": False}