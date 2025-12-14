import os
import sys
import json
import secrets
import bcrypt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status

class SessionManagerException(Exception):
    pass


def get_writable_path():
    """
    Get writable path for user data files.
    In .exe: same directory as the executable
    In dev: project root directory
    """
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    return base_path

BASE_DIR = get_writable_path()
USERS_FILE = os.path.join(BASE_DIR, "users.json")
SESSIONS_FILE = os.path.join(BASE_DIR, "sessions.json")
SESSION_DURATION = timedelta(hours=24)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except SessionManagerException as e:
        print(f"Password verification failed: {e}")
        return False


def load_users() -> Dict[str, str]:
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": hash_password("admin123"),
            "user": hash_password("user123"),
            "John": hash_password("Doe"),
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


def authenticate_user(username: str, password: str) -> bool:
    users = load_users()

    if username not in users:
        return False

    return verify_password(password, users[username])