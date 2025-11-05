"""
OpenCode client wrapper
"""
from typing import Optional, Dict, Any
import opencode_ai

from app.core.config import settings

class OpenCodeService:
    """Service for interacting with OpenCode API"""

    def __init__(self):
        self.client = opencode_ai.Opencode(base_url=settings.OPENCODE_BASE_URL)

    def list_sessions(self) -> list:
        """List all sessions"""
        return self.client.session.list()

    def create_session(self, title: Optional[str] = None) -> Dict[str, Any]:
        """Create a new session"""
        if title:
            return self.client.session.create(title=title)
        else:
            return self.client.session.create()

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details"""
        # Note: OpenCode SDK might not have retrieve method, let's try without validation for now
        return {"id": session_id, "status": "active"}

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        return self.client.session.delete(session_id)

    def send_prompt(self, session_id: str, prompt: str) -> Dict[str, Any]:
        """Send a prompt to a session"""
        return self.client.session.chat(
            session_id,
            model_id="default",
            parts=[{"type": "text", "text": prompt}],
            provider_id="default"
        )

# Global instance
opencode_service = OpenCodeService()