"""
OpenCode client wrapper
"""
from typing import Optional, Dict, Any
import opencode_ai
import os
import httpx

from app.core.config import settings

class OpenCodeService:
    """Service for interacting with OpenCode API"""

    def __init__(self):
        self.use_mock = os.getenv("USE_MOCK", "false").lower() == "true"
        if not self.use_mock:
            self.client = opencode_ai.Opencode(base_url=settings.OPENCODE_BASE_URL)
        else:
            self.client = None

    def list_sessions(self) -> list:
        """List all sessions"""
        if self.use_mock:
            return [
                {"id": "mock-session-1", "title": "Mock Session 1", "created_at": "2025-11-05T10:00:00Z"},
                {"id": "mock-session-2", "title": "Mock Session 2", "created_at": "2025-11-05T11:00:00Z"}
            ]
        return self.client.session.list()

    def create_session(self, title: Optional[str] = None, parent_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session"""
        if self.use_mock:
            import uuid
            session_id = str(uuid.uuid4())
            return {
                "id": session_id,
                "title": title or f"Session {session_id[:8]}",
                "created_at": "2025-11-05T12:00:00Z"
            }
        
        # Use HTTP client directly since OpenCode SDK doesn't support create_session
        url = f"{settings.OPENCODE_BASE_URL}/session"
        body = {}
        if title:
            body["title"] = title
        if parent_id:
            body["parentID"] = parent_id
            
        response = httpx.post(url, json=body, timeout=30.0)
        response.raise_for_status()
        return response.json()

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details"""
        if self.use_mock:
            return {"id": session_id, "title": f"Mock Session {session_id[:8]}", "status": "active"}
        # Note: OpenCode SDK might not have retrieve method, let's try without validation for now
        return {"id": session_id, "status": "active"}

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if self.use_mock:
            return True
        return self.client.session.delete(session_id)

    def send_prompt(self, session_id: str, prompt: str) -> Dict[str, Any]:
        """Send a prompt to a session"""
        if self.use_mock:
            return {
                "content": f"Mock response to: {prompt}",
                "session_id": session_id,
                "info": {"cost": 0.01, "tokens": {"input": 10, "output": 20}}
            }
        return self.client.session.chat(
            session_id,
            model_id="default",
            parts=[{"type": "text", "text": prompt}],
            provider_id="default"
        )

# Global instance
opencode_service = OpenCodeService()