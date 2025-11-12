"""
Session operations for OpenCode Agent Controller
"""

from typing import Dict, Any, List
from datetime import datetime

# In-memory session storage (use database in production)
sessions_db: Dict[str, Dict[str, Any]] = {}

def create_session(session_id: str, github_token: str = None) -> Dict[str, Any]:
    """Create a new session in storage"""
    if session_id in sessions_db:
        raise ValueError("Session already exists")

    session_data = {
        "session_id": session_id,
        "created_at": datetime.utcnow().isoformat(),
        "auth_data": None,  # Will be set by docker_ops.create_session_folder
        "container_status": None,
        "container_id": None
    }

    sessions_db[session_id] = session_data
    return session_data

def get_session(session_id: str) -> Dict[str, Any]:
    """Get session data"""
    if session_id not in sessions_db:
        raise ValueError("Session not found")
    return sessions_db[session_id]

def update_session_auth(session_id: str, auth_data: Dict[str, Any]) -> None:
    """Update session auth data"""
    if session_id not in sessions_db:
        raise ValueError("Session not found")
    sessions_db[session_id]["auth_data"] = auth_data

def update_session_container(session_id: str, container_id: str, status: str = "running") -> None:
    """Update session container info"""
    if session_id not in sessions_db:
        raise ValueError("Session not found")
    sessions_db[session_id]["container_id"] = container_id
    sessions_db[session_id]["container_status"] = status

def stop_session_container(session_id: str) -> None:
    """Mark session container as stopped"""
    if session_id not in sessions_db:
        raise ValueError("Session not found")
    sessions_db[session_id]["container_status"] = "stopped"
    sessions_db[session_id]["container_id"] = None

def list_sessions() -> List[Dict[str, Any]]:
    """List all sessions"""
    return list(sessions_db.values())

def delete_session(session_id: str) -> None:
    """Delete session from storage"""
    if session_id not in sessions_db:
        raise ValueError("Session not found")
    del sessions_db[session_id]

def session_exists(session_id: str) -> bool:
    """Check if session exists"""
    return session_id in sessions_db