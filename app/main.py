"""
FastAPI application for OpenCode UI
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

from app.core.opencode_client import opencode_service
from app.core.config import settings

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
class Model(BaseModel):
    providerID: str
    modelID: str

class CreateSessionRequest(BaseModel):
    title: Optional[str] = None

class ChatRequest(BaseModel):
    prompt: str
    model: Model

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
        response = opencode_service.send_prompt(
            session_id, 
            request.prompt,
            model=request.model
        )
        
        # Extract text content from OpenCode API response
        content = ""
        if isinstance(response, dict):
            # Handle OpenCode API response format with 'parts'
            if 'parts' in response and isinstance(response['parts'], list):
                for part in response['parts']:
                    if isinstance(part, dict) and part.get('type') == 'text' and 'text' in part:
                        content += part['text']
            # Fallback to other possible fields
            elif 'content' in response:
                content = response['content']
            elif 'message' in response:
                content = response['message']
            else:
                content = str(response)
        else:
            # Handle object responses
            if hasattr(response, 'parts') and response.parts:
                for part in response.parts:
                    if hasattr(part, 'type') and part.type == 'text' and hasattr(part, 'text'):
                        content += part.text
            elif hasattr(response, 'content'):
                content = response.content
            elif hasattr(response, 'message'):
                content = response.message
            else:
                content = str(response)
        
        return {
            "content": content.strip(),
            "session_id": session_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    """Get all messages from a session"""
    try:
        messages = opencode_service.get_messages(session_id)
        
        # Return raw messages with full details
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/models")
async def get_models():
    """Get available models from OpenCode API"""
    try:
        # Fetch providers from OpenCode API
        import httpx
        opencode_url = settings.OPENCODE_BASE_URL
        response = httpx.get(f"{opencode_url}/config/providers", timeout=30.0)
        response.raise_for_status()
        providers_data = response.json()
        
        # Transform to frontend format
        transformed_providers = []
        for provider in providers_data.get("providers", []):
            models_dict = {}
            for model_id, model_info in provider.get("models", {}).items():
                models_dict[model_id] = {
                    "id": model_id,
                    "name": model_info.get("name", model_id)
                }
            
            transformed_providers.append({
                "id": provider["id"],
                "name": provider["name"],
                "models": models_dict
            })
        
        return {
            "providers": transformed_providers,
            "default": providers_data.get("default", {})
        }
    except Exception as e:
        # Fallback to hardcoded models if OpenCode API fails
        return {
            "providers": [
                {
                    "id": "github-copilot",
                    "name": "GitHub Copilot",
                    "models": [
                        {"id": "gpt-5-mini", "name": "GPT-5 Mini"},
                        {"id": "gpt-5", "name": "GPT-5"}
                    ]
                },
                {
                    "id": "opencode",
                    "name": "OpenCode",
                    "models": [
                        {"id": "big-pickle", "name": "Big Pickle"}
                    ]
                }
            ],
            "default": {
                "github-copilot": "gpt-5-mini",
                "opencode": "big-pickle"
            }
        }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)