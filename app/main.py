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

from core.opencode_client import opencode_service
from core.config import settings
from core.database import engine, get_db, init_db
from core.models import User, Base
from core.github_oauth import get_github_oauth_service
from core.schemas import (
    LoginResponse, 
    AuthorizationUrlResponse, 
    GitHubUserResponse,
    TokenRefreshResponse
)

# Authentication dependency
async def get_current_user_dependency(request: Request, db: Session = Depends(get_db)):
    """Dependency to get current authenticated user"""
    user_id = request.cookies.get('user_id')
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
    allow_origins=["http://localhost:3000"],  # Specific origin for credentials
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
        authorization_url = get_github_oauth_service().get_main_authorization_url(state)
        
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
        device_code_data = await get_github_oauth_service().get_device_code()
        
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
async def poll_device_token(request: Request, db: Session = Depends(get_db)):
    """Poll for device code token completion"""
    try:
        request_data = await request.json()
        device_code = request_data.get("device_code")
        if not device_code:
            raise HTTPException(status_code=400, detail="Missing device_code")
        
        expires_in = request_data.get("expires_in", 900)  # Default to 15 minutes
        agent_name = request_data.get("agent_name", "").strip()
        agent_description = request_data.get("agent_description", "").strip()
        
        if not agent_name:
            raise HTTPException(status_code=400, detail="Agent name is required")
        
        # Get user from cookie
        user_id = request.cookies.get('user_id')
        if not user_id:
            raise HTTPException(status_code=401, detail="User authentication required")
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Poll for token (this will block until token is available or error occurs)
        token_response = await get_github_oauth_service().poll_for_token(device_code, expires_in=expires_in)
        
        if "error" in token_response:
            raise HTTPException(status_code=400, detail=f"Authorization failed: {token_response.get('error_description')}")
        
        # Create agent instead of authenticating user
        from core.models import Agent
        agent = Agent(
            name=agent_name,
            description=agent_description,
            access_token=token_response.get("access_token"),
            refresh_token=token_response.get("refresh_token"),
            client_id=get_github_oauth_service().copilot_client_id,  # Required field
            user_id=user.id,
            created_at=datetime.utcnow()
        )
        
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        return {
            "status": "success",
            "agent": {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "created_at": agent.created_at.isoformat()
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

        # Authenticate user using main login flow
        auth_result = await get_github_oauth_service().authenticate_main_user(code, db)
        
        # Get frontend home URL
        home_url = os.getenv("GITHUB_HOME_URL", "http://localhost:3000")
        
        # Create response with tokens in secure cookies and URL
        user_data = auth_result["user"]
        
        response = RedirectResponse(
            url=f"{home_url}?token={auth_result['access_token']}&refresh_token={auth_result.get('refresh_token', '')}",
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
        
        # Set user_id cookie for API authentication
        response.set_cookie(
            key="user_id",
            value=str(user_data.id),
            httponly=False,  # Set to True in production
            secure=False,    # Set to True in production (HTTPS only)
            samesite="lax",
            max_age=3600
        )
        
        return response

    except Exception as e:
        home_url = os.getenv("GITHUB_HOME_URL", "http://localhost:3000")
        return RedirectResponse(
            url=f"{home_url}?error={str(e)}",
            status_code=302
        )


@app.get("/auth/me", response_model=GitHubUserResponse)
async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """Get current authenticated user"""
    # Skip authentication for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        # Return a dummy response for preflight - this won't be used
        return {}
    
    user_id = request.cookies.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user.id,  # This is the GitHub user ID
        "github_login": user.github_login,
        "github_id": user.github_id or user.id,  # Fallback to id if github_id is not set
        "email": user.email,
        "avatar_url": user.avatar_url,
        "created_at": user.created_at,
        "last_login": user.last_login,
        "is_active": user.is_active
    }


@app.post("/auth/refresh-token", response_model=TokenRefreshResponse)
async def refresh_token(user_id: str, db: Session = Depends(get_db)):
    """Refresh GitHub access token"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        token_response = await get_github_oauth_service().refresh_access_token(user)
        
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
    response.delete_cookie("user_id")
    return response

# Agent Management Routes
@app.get("/api/agents")
async def list_agents(current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """List all agents for the current user"""
    try:
        from core.models import Agent
        agents = db.query(Agent).filter(Agent.user_id == current_user.id).all()
        
        return [
            {
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "created_at": agent.created_at.isoformat() if agent.created_at else None,
                "last_used": agent.last_used.isoformat() if agent.last_used else None
            }
            for agent in agents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list agents: {str(e)}")

@app.post("/api/agents")
async def create_agent(request: Dict[str, Any], current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """Create a new agent using redirect OAuth flow"""
    try:
        agent_name = request.get("name", "").strip()
        agent_description = request.get("description", "").strip()
        
        if not agent_name:
            raise HTTPException(status_code=400, detail="Agent name is required")
        
        # Generate state for OAuth
        state = secrets.token_urlsafe(32)
        
        # Store agent creation data in state (in production, use Redis/database)
        # For now, we'll store in a simple dict
        agent_creation_data = {
            "user_id": current_user.id,
            "agent_name": agent_name,
            "agent_description": agent_description,
            "state": state
        }
        
        # In a real app, store this in Redis or database with TTL
        # For demo, we'll use a global dict (not thread-safe)
        if not hasattr(create_agent, 'pending_agents'):
            create_agent.pending_agents = {}
        create_agent.pending_agents[state] = agent_creation_data
        
        # Get authorization URL for agent
        authorization_url = get_github_oauth_service().get_authorization_url(state)
        
        return {
            "authorization_url": authorization_url,
            "state": state
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create agent: {str(e)}")

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str, current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """Delete an agent"""
    try:
        from core.models import Agent
        agent = db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == current_user.id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        db.delete(agent)
        db.commit()
        
        return {"message": "Agent deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete agent: {str(e)}")

@app.get("/auth/agent/callback")
async def agent_oauth_callback(code: str = None, state: str = None, db: Session = Depends(get_db)):
    """GitHub OAuth callback handler for agent creation"""
    try:
        if not code or not state:
            raise HTTPException(status_code=400, detail="Missing authorization code or state")

        # Get agent creation data from state (in production, get from Redis/database)
        if not hasattr(create_agent, 'pending_agents') or state not in create_agent.pending_agents:
            raise HTTPException(status_code=400, detail="Invalid or expired state")
        
        agent_data = create_agent.pending_agents[state]
        del create_agent.pending_agents[state]  # Clean up
        
        # Verify user exists
        user = db.query(User).filter(User.id == agent_data["user_id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Authenticate agent (this will get the token)
        auth_result = await get_github_oauth_service().authenticate_user(code, db, is_token=False)
        
        # Create agent
        from core.models import Agent
        agent = Agent(
            name=agent_data["agent_name"],
            description=agent_data["agent_description"],
            access_token=auth_result.get("access_token"),
            refresh_token=auth_result.get("refresh_token"),
            user_id=user.id,
            created_at=datetime.utcnow()
        )
        
        db.add(agent)
        db.commit()
        db.refresh(agent)
        
        # Get frontend home URL
        home_url = os.getenv("GITHUB_HOME_URL", "http://localhost:3000")
        
        # Redirect back to agent auth page with success
        return RedirectResponse(
            url=f"{home_url}/agent-auth?success=true&agent_id={agent.id}&agent_name={agent.name}",
            status_code=302
        )

    except Exception as e:
        home_url = os.getenv("GITHUB_HOME_URL", "http://localhost:3000")
        return RedirectResponse(
            url=f"{home_url}/agent-auth?error={str(e)}",
            status_code=302
        )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)