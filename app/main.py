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
from core import models
User = models.User
Base = models.Base
Agent = models.Agent
SessionModel = models.Session
from core.github_oauth import get_github_oauth_service
from core.schemas import (
    LoginResponse, 
    AuthorizationUrlResponse, 
    GitHubUserResponse,
    TokenRefreshResponse,
    SessionCreateRequest,
    SessionResponse,
    SessionListResponse
)
from backend.routes import backend_router

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

# Include backend routes
app.include_router(backend_router)

# Pydantic models
class Model(BaseModel):
    providerID: str
    modelID: str

class CreateSessionRequest(BaseModel):
    title: Optional[str] = None

class ChatRequest(BaseModel):
    prompt: Optional[str] = None  # New format - simple prompt
    model: Optional[Model] = None
    agent: str = "build"
    parts: Optional[List[Dict[str, Any]]] = None  # Legacy format
    
    def get_prompt(self) -> str:
        """Get prompt from either new or legacy format"""
        if self.prompt:
            return self.prompt
        if self.parts and len(self.parts) > 0:
            # Extract text from first text part
            for part in self.parts:
                if isinstance(part, dict) and part.get('type') == 'text':
                    return part.get('text', '')
        return ""

class SessionResponse(BaseModel):
    id: str
    title: Optional[str] = None
    created_at: Optional[str] = None

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None

# API Routes
@app.get("/api/sessions")
async def list_sessions(current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """List all sessions"""
    import logging
    logging.warning(f"DEBUG: list_sessions called for user {current_user.id}")
    try:
        logging.warning("DEBUG: About to query sessions")
        # Since we removed the shared service, list sessions from database instead
        sessions = db.query(SessionModel).filter(SessionModel.user_id == current_user.id).all()
        logging.warning(f"DEBUG: Found {len(sessions)} sessions")
        result = [
            SessionResponse(
                id=session.session_id,
                title=session.name,
                created_at=session.created_at.isoformat() if session.created_at else None
            )
            for session in sessions
        ]
        logging.warning(f"DEBUG: Created result with {len(result)} items")
        return result
    except Exception as e:
        import logging
        logging.error(f"Error in list_sessions: {e}")
        import traceback
        logging.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(request: Optional[CreateSessionRequest] = None, current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """Create a new session"""
    try:
        # Check if user has any active agents
        from core.models import Agent
        agents = db.query(Agent).filter(Agent.user_id == current_user.id, Agent.is_active == True).all()
        
        if not agents:
            # No agent configured - return error prompting agent creation
            raise HTTPException(
                status_code=400, 
                detail="No agent configured. Please create an agent first in Settings."
            )
        
        # User has agent(s) - use the first active agent
        agent = agents[0]
        
        # Generate unique session ID (must start with 'ses' for OpenCode API)
        import uuid
        session_id = f"ses_{str(uuid.uuid4())}"
        
        # Call agent controller to create agent-based session
        import httpx
        agent_controller_url = os.getenv("AGENT_CONTROLLER_URL", "http://localhost:8001")
        service_secret = os.getenv("AGENT_SERVICE_SECRET", "default-secret-change-in-production")
        
        # Create agent session via agent controller
        response = httpx.post(
            f"{agent_controller_url}/sessions/agent",
            json={
                "session_id": session_id,
                "agent_id": agent.id,
                "agent_token": agent.access_token,
                "title": request.title if request else None
            },
            headers={"X-Service-Secret": service_secret},
            timeout=60.0
        )
        response.raise_for_status()
        agent_session_data = response.json()
        
        # Create session in database
        db_session = SessionModel(
            session_id=session_id,
            user_id=current_user.id,
            agent_id=agent.id,
            name=request.title if request else None,
            status="active",
            is_active=True,
            container_id=agent_session_data.get("container_id"),
            container_status=agent_session_data.get("container_status"),
            base_url=agent_session_data.get("base_url"),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        # Update agent last_used
        agent.last_used = datetime.utcnow()
        db.commit()
        
        return SessionResponse(
            id=session_id,
            title=request.title if request else None,
            created_at=db_session.created_at.isoformat() if db_session.created_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        if "not supported" in error_msg.lower():
            raise HTTPException(status_code=400, detail="Creating new sessions is not supported. Please select an existing session from the list.")
        raise HTTPException(status_code=500, detail=f"Failed to create session: {error_msg}")

@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str, current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """Get session details"""
    try:
        # Get session from database instead of shared service
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id,
            SessionModel.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            id=session.session_id,
            title=session.name,
            created_at=session.created_at.isoformat() if session.created_at else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Session not found: {str(e)}")

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """Delete a session"""
    try:
        # Get session from database
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id,
            SessionModel.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # TODO: Clean up agent container if it exists
        # For now, just delete from database
        db.delete(session)
        db.commit()
        
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@app.post("/api/sessions/{session_id}/chat")
async def chat(session_id: str, request: ChatRequest, current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """Send a chat message"""
    try:
        # Check if this is a database session
        db_session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id,
            SessionModel.user_id == current_user.id
        ).first()
        
        if not db_session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Session must have container ID
        if not db_session.container_id:
            raise HTTPException(
                status_code=400, 
                detail="Session has no running container"
            )
        
        # Get the prompt from either new or legacy format
        prompt = request.get_prompt()
        
        if not prompt:
            raise HTTPException(status_code=400, detail="No prompt provided")
        
        # Forward the message directly to the agent container
        import requests as sync_requests
        base_url = db_session.base_url or f"http://agent_{session_id}:4096"
        
        try:
            response = sync_requests.post(
                f"{base_url}/session/{session_id}/chat",
                json={"prompt": prompt},
                timeout=30
            )
            
            # Update session last_activity
            db_session.last_activity = datetime.utcnow()
            db.commit()
            
            # Return the response
            return {
                "content": f"Message sent to container (status: {response.status_code})",
                "session_id": session_id,
                "container_status": response.status_code
            }
        except sync_requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=502,
                detail=f"Failed to reach container at {base_url}: {str(e)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Error sending chat message for session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")

@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """Get all messages from a session"""
    try:
        # Check if session exists in database
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id,
            SessionModel.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Use agent-specific service to get messages
        if not session.base_url:
            raise HTTPException(status_code=400, detail="Session is not properly configured")
        
        from core.opencode_client import get_opencode_service
        agent_service = get_opencode_service(base_url=session.base_url)
        
        # For agent containers, we need to create an OpenCode session
        # Try to create a session in the agent
        try:
            session_response = agent_service.create_session(title=session.name or f"Session {session_id[:8]}")
            if isinstance(session_response, dict) and 'id' in session_response:
                opencode_session_id = session_response['id']
            else:
                # Fallback to using the database session ID
                opencode_session_id = session_id
        except Exception as create_error:
            import logging
            logging.warning(f"Could not create OpenCode session: {create_error}")
            # Fallback to using the database session ID
            opencode_session_id = session_id
        
        # Check if session exists in agent, create if not
        try:
            messages = agent_service.get_messages(opencode_session_id)
        except Exception:
            # Session doesn't exist in agent, create it
            try:
                agent_service.create_session(title=session.name or f"Session {session_id[:8]}")
                messages = []  # New session has no messages
            except Exception as create_error:
                import logging
                logging.warning(f"Could not create session in agent: {create_error}")
                messages = []  # Return empty messages if we can't create session
        
        # Return raw messages with full details
        return messages
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Error getting messages for session {session_id}: {str(e)}")
        # If the agent container is not available, return empty messages
        if "Name or service not known" in str(e) or "Connection refused" in str(e):
            return []
        raise HTTPException(status_code=500, detail=f"Failed to get messages: {str(e)}")

# Database-backed Session Management Routes
@app.get("/api/db/sessions", response_model=SessionListResponse)
async def list_db_sessions(current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """List all database sessions for the current user"""
    try:
        sessions = db.query(SessionModel).filter(SessionModel.user_id == current_user.id).all()
        
        return SessionListResponse(
            sessions=[
                SessionResponse(
                    id=session.id,
                    session_id=session.session_id,
                    user_id=session.user_id,
                    agent_id=session.agent_id,
                    name=session.name,
                    description=session.description,
                    status=session.status,
                    is_active=session.is_active,
                    container_id=session.container_id,
                    container_status=session.container_status,
                    base_url=session.base_url,
                    auth_data=session.auth_data,
                    environment_vars=session.environment_vars,
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                    last_activity=session.last_activity
                )
                for session in sessions
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")

@app.post("/api/db/sessions", response_model=SessionResponse)
async def create_db_session(request: SessionCreateRequest, current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """Create a new database session for the current user"""
    try:
        # Check if session_id already exists for this user
        existing_session = db.query(SessionModel).filter(
            SessionModel.session_id == request.session_id,
            SessionModel.user_id == current_user.id
        ).first()
        
        if existing_session:
            raise HTTPException(status_code=409, detail="Session with this ID already exists")
        
        # Create new session
        session = SessionModel(
            session_id=request.session_id,
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            status="active",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return SessionResponse(
            id=session.id,
            session_id=session.session_id,
            user_id=session.user_id,
            name=session.name,
            description=session.description,
            status=session.status,
            is_active=session.is_active,
            container_id=session.container_id,
            container_status=session.container_status,
            auth_data=session.auth_data,
            environment_vars=session.environment_vars,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_activity=session.last_activity
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.get("/api/db/sessions/{session_id}", response_model=SessionResponse)
async def get_db_session(session_id: str, current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """Get a specific database session"""
    try:
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id,
            SessionModel.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return SessionResponse(
            id=session.id,
            session_id=session.session_id,
            user_id=session.user_id,
            agent_id=session.agent_id,
            name=session.name,
            description=session.description,
            status=session.status,
            is_active=session.is_active,
            container_id=session.container_id,
            container_status=session.container_status,
            base_url=session.base_url,
            auth_data=session.auth_data,
            environment_vars=session.environment_vars,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_activity=session.last_activity
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")

@app.put("/api/db/sessions/{session_id}")
async def update_db_session(session_id: str, request: SessionCreateRequest, current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """Update a database session"""
    try:
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id,
            SessionModel.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update fields
        session.name = request.name
        session.description = request.description
        session.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(session)
        
        return SessionResponse(
            id=session.id,
            session_id=session.session_id,
            user_id=session.user_id,
            agent_id=session.agent_id,
            name=session.name,
            description=session.description,
            status=session.status,
            is_active=session.is_active,
            container_id=session.container_id,
            container_status=session.container_status,
            base_url=session.base_url,
            auth_data=session.auth_data,
            environment_vars=session.environment_vars,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_activity=session.last_activity
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update session: {str(e)}")

@app.delete("/api/db/sessions/{session_id}")
async def delete_db_session(session_id: str, current_user: User = Depends(get_current_user_dependency), db: Session = Depends(get_db)):
    """Delete a database session"""
    try:
        session = db.query(SessionModel).filter(
            SessionModel.session_id == session_id,
            SessionModel.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        db.delete(session)
        db.commit()
        
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete session: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/api/models")
async def get_models(current_user: User = Depends(get_current_user_dependency)):
    """Get available models from OpenCode API"""
    try:
        # Fetch models from agent containers via backend API
        # We need to get a running agent container to query its /config/providers endpoint
        
        # For now, try to get models from a running container
        # In production, this should be cached and refreshed periodically
        
        # Try to find an active session with a running container
        from core.database import get_db
        from core.models import Session
        
        db = next(get_db())
        try:
            # Find the most recent active session with a container
            active_session = db.query(Session).filter(
                Session.user_id == current_user.id,
                Session.is_active == True,
                Session.container_id.isnot(None)
            ).order_by(Session.last_activity.desc()).first()
            
            if active_session and active_session.base_url:
                # Query the agent container for providers
                import requests
                try:
                    providers_url = f"{active_session.base_url}/config/providers"
                    response = requests.get(providers_url, timeout=5)
                    
                    if response.status_code == 200:
                        providers_data = response.json()
                        
                        # Transform the data to match frontend expectations
                        transformed_providers = []
                        default_config = {}
                        
                        for provider_data in providers_data.get("providers", []):
                            provider_id = provider_data.get("id")
                            provider_name = provider_data.get("name", provider_id)
                            
                            # Transform models dict to array format expected by frontend
                            models_dict = provider_data.get("models", {})
                            models_array = []
                            
                            for model_id, model_info in models_dict.items():
                                if isinstance(model_info, dict):
                                    models_array.append({
                                        "id": model_id,
                                        "name": model_info.get("name", model_id)
                                    })
                                else:
                                    # Handle case where model_info is just a string
                                    models_array.append({
                                        "id": model_id,
                                        "name": str(model_info)
                                    })
                            
                            transformed_providers.append({
                                "id": provider_id,
                                "name": provider_name,
                                "models": models_array
                            })
                        
                        # Get default provider/model
                        defaults = providers_data.get("default", {})
                        if defaults:
                            for provider_id, model_id in defaults.items():
                                default_config[provider_id] = model_id
                        
                        return {
                            "providers": transformed_providers,
                            "default": default_config
                        }
                        
                except requests.RequestException as e:
                    print(f"Failed to fetch providers from container: {e}")
        
        finally:
            db.close()
        
        # Fallback to hardcoded models if no active container or fetch failed
        return {
            "providers": [
                {
                    "id": "opencode",
                    "name": "OpenCode",
                    "models": [
                        {"id": "grok-code", "name": "Grok Code Fast 1"},
                        {"id": "big-pickle", "name": "Big Pickle"}
                    ]
                }
            ],
            "default": {
                "opencode": "grok-code"
            }
        }
    except Exception as e:
        print(f"Error fetching models: {e}")
        # Fallback to hardcoded models
        return {
            "providers": [
                {
                    "id": "opencode",
                    "name": "OpenCode",
                    "models": [
                        {"id": "grok-code", "name": "Grok Code Fast 1"},
                        {"id": "big-pickle", "name": "Big Pickle"}
                    ]
                }
            ],
            "default": {
                "opencode": "grok-code"
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
        
        # Create response with tokens in secure cookies only (no URL tokens for security)
        user_data = auth_result["user"]
        
        response = RedirectResponse(
            url=home_url,  # Redirect to home page without tokens in URL
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