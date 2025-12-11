import os
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, status

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