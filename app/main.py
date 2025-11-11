"""
FastAPI application for OpenCode UI
"""
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import secrets
import os
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.opencode_client import opencode_service
from app.core.config import settings
from app.core.database import engine, get_db, init_db
from app.core.models import User, Base
from app.core.github_oauth import github_oauth_service
from app.core.schemas import (
    LoginResponse, 
    AuthorizationUrlResponse, 
    GitHubUserResponse,
    TokenRefreshResponse
)

# Authentication dependency
async def get_current_user_dependency(request: Request, db: Session = Depends(get_db)):
    """Dependency to get current authenticated user"""
    user_id = request.headers.get('X-User-ID')
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

# Create database tables
init_db()

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
async def list_sessions(current_user: User = Depends(get_current_user_dependency)):
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
async def create_session(request: Optional[CreateSessionRequest] = None, current_user: User = Depends(get_current_user_dependency)):
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
async def get_session(session_id: str, current_user: User = Depends(get_current_user_dependency)):
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
async def delete_session(session_id: str, current_user: User = Depends(get_current_user_dependency)):
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
async def chat(session_id: str, request: ChatRequest, current_user: User = Depends(get_current_user_dependency)):
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
async def get_session_messages(session_id: str, current_user: User = Depends(get_current_user_dependency)):
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
async def get_models(current_user: User = Depends(get_current_user_dependency)):
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

# OAuth/Authentication Routes
@app.get("/auth/login", response_model=AuthorizationUrlResponse)
async def get_login_url():
    """Get GitHub OAuth authorization URL"""
    try:
        state = secrets.token_urlsafe(32)
        # Store state in a simple in-memory dict (in production, use Redis or database)
        # For now, we'll just return it and validate it later
        authorization_url = github_oauth_service.get_authorization_url(state)
        
        return {
            "authorization_url": authorization_url,
            "state": state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate login URL: {str(e)}")


@app.get("/auth/device", response_model=Dict[str, Any])
async def get_device_code():
    """Get GitHub OAuth device code for authentication"""
    try:
        device_code_data = await github_oauth_service.get_device_code()
        
        return {
            "device_code": device_code_data.get("device_code"),
            "user_code": device_code_data.get("user_code"),
            "verification_uri": device_code_data.get("verification_uri"),
            "expires_in": device_code_data.get("expires_in"),
            "interval": device_code_data.get("interval", 5)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get device code: {str(e)}")


@app.post("/auth/device/poll")
async def poll_device_token(request: Dict[str, Any], db: Session = Depends(get_db)):
    """Poll for device code token completion"""
    try:
        device_code = request.get("device_code")
        if not device_code:
            raise HTTPException(status_code=400, detail="Missing device_code")
        
        expires_in = request.get("expires_in", 900)  # Default to 15 minutes
        
        # Poll for token (this will block until token is available or error occurs)
        token_response = await github_oauth_service.poll_for_token(device_code, expires_in=expires_in)
        
        if "error" in token_response:
            raise HTTPException(status_code=400, detail=f"Authorization failed: {token_response.get('error_description')}")
        
        # Exchange the token for user authentication (reuse existing logic)
        # Token will be stored in database, not returned to frontend
        auth_result = await github_oauth_service.authenticate_user(token_response.get("access_token"), db, is_token=True)
        
        return {
            "status": "success",
            "user": {
                "id": auth_result["user"].id,
                "login": auth_result["user"].github_login,
                "email": auth_result["user"].email,
                "avatar_url": auth_result["user"].avatar_url
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to poll token: {str(e)}")


@app.get("/auth/callback")
async def oauth_callback(code: str = None, state: str = None, db: Session = Depends(get_db)):
    """GitHub OAuth callback handler"""
    try:
        if not code:
            raise HTTPException(status_code=400, detail="Missing authorization code")

        # Authenticate user and get tokens
        auth_result = await github_oauth_service.authenticate_user(code, db)
        
        # Get frontend home URL
        home_url = os.getenv("GITHUB_HOME_URL", "http://localhost:3000")
        
        # Create response with tokens in secure cookies and URL
        user_data = auth_result["user"]
        
        response = RedirectResponse(
            url=f"{home_url}?token={auth_result['access_token']}&refresh_token={auth_result.get('refresh_token', '')}&user_id={user_data.id}",
            status_code=302
        )
        
        # Set secure cookies (production: use HttpOnly, Secure flags)
        response.set_cookie(
            key="access_token",
            value=auth_result["access_token"],
            httponly=False,  # Set to True in production
            secure=False,    # Set to True in production (HTTPS only)
            samesite="lax",
            max_age=3600
        )
        
        if auth_result.get("refresh_token"):
            response.set_cookie(
                key="refresh_token",
                value=auth_result["refresh_token"],
                httponly=False,  # Set to True in production
                secure=False,    # Set to True in production (HTTPS only)
                samesite="lax",
                max_age=604800  # 7 days
            )
        
        return response

    except Exception as e:
        home_url = os.getenv("GITHUB_HOME_URL", "http://localhost:3000")
        return RedirectResponse(
            url=f"{home_url}?error={str(e)}",
            status_code=302
        )


@app.get("/auth/me", response_model=GitHubUserResponse)
async def get_current_user(current_user: User = Depends(get_current_user_dependency)):
    """Get current authenticated user"""
    return {
        "id": current_user.id,
        "login": current_user.github_login,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url
    }


@app.post("/auth/refresh-token", response_model=TokenRefreshResponse)
async def refresh_token(user_id: str, db: Session = Depends(get_db)):
    """Refresh GitHub access token"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        token_response = await github_oauth_service.refresh_access_token(user)
        
        # Update user in database
        user.access_token = token_response.get("access_token")
        if token_response.get("refresh_token"):
            user.refresh_token = token_response.get("refresh_token")
        
        db.commit()
        
        return {
            "access_token": token_response.get("access_token"),
            "refresh_token": token_response.get("refresh_token"),
            "token_type": token_response.get("token_type", "bearer"),
            "expires_in": token_response.get("expires_in")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh token: {str(e)}")


@app.get("/auth/logout")
async def logout():
    """Logout user"""
    response = JSONResponse({"message": "Logged out successfully"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)