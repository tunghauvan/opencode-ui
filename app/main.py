"""
FastAPI application for OpenCode UI
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

from app.core.opencode_client import opencode_service

app = FastAPI(title="OpenCode UI API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class CreateSessionRequest(BaseModel):
    title: Optional[str] = None

class ChatRequest(BaseModel):
    prompt: str

class SessionResponse(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: Optional[str] = None

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

# API Routes
@app.get("/api/sessions", response_model=List[SessionResponse])
async def list_sessions():
    """List all sessions"""
    try:
        sessions = opencode_service.list_sessions()
        return [
            SessionResponse(
                id=session.get('id') if isinstance(session, dict) else session.id,
                title=session.get('title') if isinstance(session, dict) else getattr(session, 'title', None),
                created_at=session.get('created_at') if isinstance(session, dict) else getattr(session, 'created_at', None)
            )
            for session in sessions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(request: Optional[CreateSessionRequest] = None):
    """Create a new session"""
    try:
        title = request.title if request else None
        session = opencode_service.create_session(title)
        return SessionResponse(
            id=session.get('id') if isinstance(session, dict) else session.id,
            title=session.get('title') if isinstance(session, dict) else getattr(session, 'title', None),
            created_at=session.get('created_at') if isinstance(session, dict) else getattr(session, 'created_at', None)
        )
    except Exception as e:
        error_msg = str(e)
        if "not supported" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Creating new sessions is not supported. Please select an existing session from the list.")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {error_msg}")

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session details"""
    try:
        session = opencode_service.get_session(session_id)
        return SessionResponse(
            id=session.get('id', session_id),
            title=session.get('title'),
            created_at=session.get('created_at')
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    try:
        result = opencode_service.delete_session(session_id)
        if result:
            return {"message": "Session deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@app.post("/api/sessions/{session_id}/chat")
async def chat(session_id: str, request: ChatRequest):
    """Send a chat message"""
    try:
        response = opencode_service.send_prompt(session_id, request.prompt)
        # Handle different response formats
        if hasattr(response, 'content'):
            content = response.content
        elif hasattr(response, 'message'):
            content = response.message
        elif isinstance(response, dict):
            content = response.get('content', response.get('message', str(response)))
        else:
            # Handle AssistantMessage object with parts
            content = ""
            if hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    if isinstance(part, dict) and part.get('type') == 'text' and 'text' in part:
                        content += part['text']
            else:
                content = str(response)
        
        return {
            "content": content.strip(),
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)