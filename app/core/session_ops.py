"""
Session operations for OpenCode Agent Controller using persistent database storage
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .database import SessionLocal
from .models import Session

# Database session for agent controller operations
def get_db_session():
    """Get database session"""
    db = SessionLocal()
    return db

def create_session(session_id: str, github_token: str = None) -> Dict[str, Any]:
    """Create a new session in persistent storage"""
    db = get_db_session()
    try:
        # Check if session already exists
        existing = db.query(Session).filter(Session.session_id == session_id).first()
        if existing:
            raise ValueError("Session already exists")

        # Create new session record
        session = Session(
            session_id=session_id,
            user_id="agent-controller",  # Agent controller sessions are system sessions
            status="active",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session_to_dict(session)
    finally:
        db.close()

def get_session(session_id: str) -> Dict[str, Any]:
    """Get session data from persistent storage"""
    db = get_db_session()
    try:
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")
        return session_to_dict(session)
    finally:
        db.close()

def update_session_auth(session_id: str, auth_data: Dict[str, Any]) -> None:
    """Update session auth data in persistent storage"""
    db = get_db_session()
    try:
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")
        
        session.auth_data = json.dumps(auth_data)
        session.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()

def update_session_container(session_id: str, container_id: str, status: str = "running", opencode_session_id: str = None) -> None:
    """Update session container info in persistent storage"""
    db = get_db_session()
    try:
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")
        
        session.container_id = container_id
        session.container_status = status
        session.updated_at = datetime.utcnow()
        
        # Store OpenCode session ID directly in the model
        if opencode_session_id:
            session.opencode_session_id = opencode_session_id
            print(f"Stored OpenCode session ID: {opencode_session_id} for session: {session_id}")
        
        db.commit()
    finally:
        db.close()

def stop_session_container(session_id: str) -> None:
    """Mark session container as stopped in persistent storage"""
    db = get_db_session()
    try:
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")
        
        session.container_status = "stopped"
        session.container_id = None
        session.updated_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()

def list_sessions() -> List[Dict[str, Any]]:
    """List all sessions from persistent storage"""
    db = get_db_session()
    try:
        sessions = db.query(Session).all()
        return [session_to_dict(s) for s in sessions]
    finally:
        db.close()

def delete_session(session_id: str) -> None:
    """Delete session from persistent storage"""
    db = get_db_session()
    try:
        session = db.query(Session).filter(Session.session_id == session_id).first()
        if not session:
            raise ValueError("Session not found")
        
        db.delete(session)
        db.commit()
    finally:
        db.close()

def session_exists(session_id: str) -> bool:
    """Check if session exists in persistent storage"""
    db = get_db_session()
    try:
        session = db.query(Session).filter(Session.session_id == session_id).first()
        return session is not None
    finally:
        db.close()

def session_to_dict(session: Session) -> Dict[str, Any]:
    """Convert Session model to dictionary"""
    return {
        "id": session.id,
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "auth_data": json.loads(session.auth_data) if session.auth_data else None,
        "container_status": session.container_status,
        "container_id": session.container_id,
        "status": session.status,
        "is_active": session.is_active,
        "opencode_session_id": session.opencode_session_id
    }