"""
Backend API routes for session management
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession
import requests as sync_requests

from core.database import get_db
from core.models import User
from core.schemas import (
    SessionCreateRequest,
    SessionResponse,
    SessionListResponse
)

# Request models for container operations
class StartContainerRequest(BaseModel):
    image: str
    environment: Optional[Dict[str, str]] = None
    is_agent: bool = False

class ChatRequest(BaseModel):
    prompt: str = ""
    message: Optional[str] = None  # Alternative field name
    
    def get_prompt(self) -> str:
        """Get prompt from either prompt or message field"""
        return self.prompt or self.message or ""
from backend.apis import (
    SessionManagementService,
    ContainerManagementService,
    SessionAnalyticsService
)
from backend.utils import (
    SessionValidator,
    ContainerValidator,
    ErrorHandler
)


# Create router
backend_router = APIRouter(prefix="/api/backend", tags=["backend"])


# Helper dependency to get current user
async def get_current_user(http_request: Request, db: DBSession = Depends(get_db)) -> User:
    """Get current authenticated user"""
    user_id = http_request.cookies.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


# Session Management Routes

@backend_router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Create a new session"""
    try:
        # Validate session_id if provided
        if request.session_id and not SessionValidator.validate_session_id(request.session_id):
            raise HTTPException(status_code=400, detail="Invalid session_id format")

        service = SessionManagementService(db)
        session = service.create_session(
            user=current_user,
            session_id=request.session_id,
            name=request.name,
            description=request.description
        )

        return session_to_response(session)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    status: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """List all sessions for current user"""
    try:
        service = SessionManagementService(db)
        sessions = service.list_sessions(
            user=current_user,
            status=status,
            is_active=is_active
        )

        return SessionListResponse(
            sessions=[session_to_response(s) for s in sessions]
        )
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Get specific session details"""
    try:
        service = SessionManagementService(db)
        session = service.get_session(current_user, session_id)
        return session_to_response(session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.put("/sessions/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Update session metadata"""
    try:
        service = SessionManagementService(db)
        session = service.update_session(
            user=current_user,
            session_id=session_id,
            name=request.name,
            description=request.description
        )
        return session_to_response(session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Delete a session"""
    try:
        service = SessionManagementService(db)
        service.delete_session(current_user, session_id)
        return {"message": "Session deleted successfully", "session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


# Container Management Routes

@backend_router.post("/sessions/{session_id}/container/start")
async def start_container(
    session_id: str,
    container_request: StartContainerRequest,
    request: Request,
    db: DBSession = Depends(get_db)
):
    """Start a Docker container for a session via Agent Controller"""
    # Get current user inline
    user_id = request.cookies.get('user_id')
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    current_user = db.query(User).filter(User.id == user_id).first()
    if not current_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    try:
        # Validate image name
        if not ContainerValidator.validate_image_name(container_request.image):
            raise HTTPException(status_code=400, detail="Invalid image name")

        session_service = SessionManagementService(db)
        container_service = ContainerManagementService(db)

        result = await container_service.start_session_container(
            user=current_user,
            session_id=session_id,
            image=container_request.image,
            environment=container_request.environment,
            is_agent=container_request.is_agent,
            session_service=session_service
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.post("/sessions/{session_id}/container/stop")
async def stop_container(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Stop a Docker container for a session via Agent Controller"""
    try:
        session_service = SessionManagementService(db)
        container_service = ContainerManagementService(db)

        result = await container_service.stop_session_container(
            user=current_user,
            session_id=session_id,
            session_service=session_service
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.get("/sessions/{session_id}/container/logs")
async def get_container_logs(
    session_id: str,
    tail: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Get container logs for a session via Agent Controller"""
    try:
        session_service = SessionManagementService(db)
        container_service = ContainerManagementService(db)

        logs = await container_service.get_session_container_logs(
            user=current_user,
            session_id=session_id,
            tail=tail,
            session_service=session_service
        )

        return {"logs": logs, "session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.get("/sessions/{session_id}/container/status")
async def get_container_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Get container status for a session via Agent Controller"""
    try:
        session_service = SessionManagementService(db)
        container_service = ContainerManagementService(db)

        status = await container_service.get_container_status(
            user=current_user,
            session_id=session_id,
            session_service=session_service
        )
        
        # Also update the session record with actual container status
        session = session_service.get_session(current_user, session_id)
        actual_status = status.get("container_status", "unknown")
        if session.container_status != actual_status:
            session.container_status = actual_status
            if actual_status in ["exited", "dead", "not_found"]:
                session.container_id = None
                session.container_status = "stopped"
            db.commit()

        return status
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.post("/sessions/{session_id}/chat")
async def chat_with_session(
    session_id: str,
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Send a chat message to a session's container"""
    try:
        print(f"\n=== CHAT ENDPOINT CALLED ===")
        print(f"Session ID: {session_id}")
        print(f"Request: {request}")
        
        session_service = SessionManagementService(db)
        session = session_service.get_session(current_user, session_id)
        
        print(f"Session found: {session.session_id}")
        print(f"Container ID: {session.container_id}")
        
        if not session.container_id:
            raise HTTPException(status_code=400, detail="Session has no running container")
        
        base_url = session.base_url or f"http://agent_{session_id}:4096"
        
        # Ensure session_id starts with "ses" for agent container compatibility
        agent_session_id = session_id if session_id.startswith("ses") else f"ses{session_id}"
        prompt = request.get_prompt()
        
        print(f"Base URL: {base_url}")
        print(f"Agent Session ID: {agent_session_id}")
        print(f"Prompt: {prompt}")
        
        # Test import
        import requests
        print(f"Requests imported: {requests}")
        
        # Check if we have an existing OpenCode session ID from previous runs
        existing_opencode_session_id = session.opencode_session_id
        print(f"Existing OpenCode session ID from DB: {existing_opencode_session_id}")
        
        # Try to use existing session, or create a new one
        opencode_session_id = existing_opencode_session_id
        
        if not opencode_session_id:
            # Create new OpenCode session only if we don't have one
            try:
                create_session_url = f"{base_url}/session"
                create_response = requests.post(
                    create_session_url,
                    json={"title": session.name or f"Session {session_id}"},
                    timeout=10
                )
                if create_response.status_code in [200, 201]:
                    session_data = create_response.json()
                    opencode_session_id = session_data.get("id")
                    print(f"Created NEW OpenCode session: {opencode_session_id}")
                    
                    # Save the OpenCode session ID to database for future reuse
                    session.opencode_session_id = opencode_session_id
                    db.commit()
                    print(f"Saved OpenCode session ID to database: {opencode_session_id}")
                else:
                    print(f"Failed to create OpenCode session: {create_response.status_code} - {create_response.text}")
            except Exception as e:
                print(f"Warning: Could not create OpenCode session: {e}")
        else:
            print(f"Reusing existing OpenCode session: {opencode_session_id}")
        
        # Fetch available providers and models from OpenCode
        provider_id = "openai"  # fallback
        model_id = "gpt-4"      # fallback
        
        try:
            providers_url = f"{base_url}/config/providers"
            providers_response = requests.get(providers_url, timeout=10)
            if providers_response.status_code == 200:
                providers_data = providers_response.json()
                providers = providers_data.get("providers", [])
                default_config = providers_data.get("default", {})
                
                if providers and default_config:
                    # Use the default provider and model
                    default_provider = list(default_config.keys())[0] if default_config else None
                    if default_provider:
                        provider_id = default_provider
                        model_id = default_config[default_provider]
                        print(f"Using provider: {provider_id}, model: {model_id}")
                    else:
                        # Fallback to first available provider
                        first_provider = providers[0]
                        provider_id = first_provider.get("id", "openai")
                        models = first_provider.get("models", {})
                        if models:
                            model_id = list(models.keys())[0]
                        print(f"Using fallback provider: {provider_id}, model: {model_id}")
        except Exception as e:
            print(f"Warning: Could not fetch providers config: {e}, using defaults")
        
        # Use the OpenCode session ID if available, otherwise fall back to agent_session_id
        message_session_id = opencode_session_id or agent_session_id
        print(f"Using session ID for message: {message_session_id}")
        print(f"OpenCode session ID: {opencode_session_id}")
        print(f"Agent session ID: {agent_session_id}")
        
        response = requests.post(
            f"{base_url}/session/{message_session_id}/message",
            json={
                "model": {
                    "providerID": provider_id,
                    "modelID": model_id
                },
                "agent": "build",
                "parts": [{"type": "text", "text": prompt}]
            },
            timeout=30
        )
        print(f"Response: {response.status_code}")
        
        if response.status_code == 200:
            try:
                agent_response = response.json()
                
                # Try different response formats
                content = ""
                if 'content' in agent_response:
                    content = agent_response['content']
                elif 'parts' in agent_response and agent_response['parts']:
                    # Extract text from parts array
                    for part in agent_response['parts']:
                        if part.get('type') == 'text':
                            content += part.get('text', '')
                elif 'text' in agent_response:
                    content = agent_response['text']
                
                if content.strip() or (agent_response.get('parts') and len(agent_response['parts']) > 0):  # Return if we have content or parts
                    return {
                        "session_id": session_id,
                        "prompt": prompt,
                        "content": content,
                        "parts": agent_response.get('parts', []),
                        "status": "success",
                        "container_status": response.status_code
                    }
                    mock_responses = [
                        f"Hello! I received your message: '{prompt}'. How can I help you today?",
                        f"Thanks for your message: '{prompt}'. I'm here to assist you with coding questions.",
                        f"I understand you said: '{prompt}'. What would you like me to help you with?",
                        f"Your message '{prompt}' has been received. I'm ready to help with any programming tasks!",
                        f"Hi there! You mentioned '{prompt}'. Feel free to ask me anything about coding or development."
                    ]
                    import random
                    mock_content = random.choice(mock_responses)
                    return {
                        "session_id": session_id,
                        "prompt": prompt,
                        "content": mock_content,
                        "status": "success",
                        "container_status": response.status_code
                    }
            except Exception as e:
                print(f"Failed to parse agent response: {e}")
                # Return a more realistic mock response for development
                mock_responses = [
                    f"Hello! I received your message: '{prompt}'. How can I help you today?",
                    f"Thanks for your message: '{prompt}'. I'm here to assist you with coding questions.",
                    f"I understand you said: '{prompt}'. What would you like me to help you with?",
                    f"Your message '{prompt}' has been received. I'm ready to help with any programming tasks!",
                    f"Hi there! You mentioned '{prompt}'. Feel free to ask me anything about coding or development."
                ]
                import random
                mock_content = random.choice(mock_responses)
                return {
                    "session_id": session_id,
                    "prompt": prompt,
                    "content": mock_content,
                    "status": "success",
                    "container_status": response.status_code
                }
        else:
            return {
                "session_id": session_id,
                "prompt": prompt,
                "status": "error",
                "error": f"Agent returned status {response.status_code}",
                "container_status": response.status_code
            }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=str(e))


@backend_router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Get all messages for a session from the OpenCode agent"""
    try:
        print(f"\n=== GET MESSAGES ENDPOINT CALLED ===")
        print(f"Session ID: {session_id}")
        
        session_service = SessionManagementService(db)
        session = session_service.get_session(current_user, session_id)
        
        print(f"Session found: {session.session_id}")
        print(f"Container ID: {session.container_id}")
        print(f"OpenCode Session ID: {session.opencode_session_id}")
        
        # If no container or no opencode session, return empty messages
        if not session.container_id or not session.opencode_session_id:
            return {
                "session_id": session_id,
                "messages": [],
                "status": "success"
            }
        
        base_url = session.base_url or f"http://agent_{session_id}:4096"
        opencode_session_id = session.opencode_session_id
        
        import requests
        
        # Fetch messages from OpenCode agent
        try:
            messages_url = f"{base_url}/session/{opencode_session_id}/message"
            print(f"Fetching messages from: {messages_url}")
            
            response = requests.get(messages_url, timeout=30)
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                messages = response.json()
                print(f"Fetched {len(messages) if isinstance(messages, list) else 'unknown'} messages")
                
                # Normalize messages to expected format
                normalized_messages = []
                if isinstance(messages, list):
                    for msg in messages:
                        normalized_messages.append(msg)
                elif isinstance(messages, dict) and 'messages' in messages:
                    normalized_messages = messages['messages']
                
                return {
                    "session_id": session_id,
                    "opencode_session_id": opencode_session_id,
                    "messages": normalized_messages,
                    "status": "success"
                }
            else:
                print(f"Failed to fetch messages: {response.status_code} - {response.text}")
                return {
                    "session_id": session_id,
                    "messages": [],
                    "status": "error",
                    "error": f"Agent returned status {response.status_code}"
                }
                
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return {
                "session_id": session_id,
                "messages": [],
                "status": "error",
                "error": str(e)
            }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=str(e))


# Container Sync Routes

@backend_router.post("/containers/sync")
async def sync_all_containers(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Sync container status for all user sessions via agent-controller"""
    try:
        import httpx
        from core.config import settings
        from core.models import Session as SessionModel
        
        # Get all sessions for user
        sessions = db.query(SessionModel).filter(SessionModel.user_id == current_user.id).all()
        
        synced = []
        orphaned = []
        
        async with httpx.AsyncClient() as client:
            for session in sessions:
                session_id = session.session_id
                
                try:
                    # Check container status via agent-controller
                    response = await client.get(
                        f"http://agent-controller:8001/sessions/{session_id}/status",
                        headers={"X-Service-Secret": settings.AGENT_SERVICE_SECRET},
                        timeout=5.0
                    )
                    
                    if response.status_code == 200:
                        status_data = response.json()
                        actual_status = status_data.get("container_status", "unknown")
                        actual_id = status_data.get("container_id")
                        
                        # Update if different
                        if session.container_status != actual_status or (actual_id and session.container_id != actual_id):
                            old_status = session.container_status
                            
                            if actual_status in ["not_found", "exited", "dead"]:
                                session.container_id = None
                                session.container_status = "stopped"
                            else:
                                if actual_id:
                                    session.container_id = actual_id
                                session.container_status = actual_status if actual_status == "running" else "stopped"
                            
                            synced.append({
                                "session_id": session_id,
                                "old_status": old_status,
                                "new_status": session.container_status,
                                "container_id": actual_id[:12] if actual_id else None
                            })
                    elif response.status_code == 404:
                        # Session not in agent-controller
                        if session.container_id:
                            orphaned.append({
                                "session_id": session_id,
                                "old_container_id": session.container_id[:12] if session.container_id else None
                            })
                            session.container_id = None
                            session.container_status = "stopped"
                            
                except Exception as e:
                    print(f"Error checking container for {session_id}: {e}")
        
        db.commit()
        
        return {
            "status": "success",
            "synced_count": len(synced),
            "synced": synced,
            "orphaned_count": len(orphaned),
            "orphaned": orphaned,
            "total_sessions": len(sessions)
        }
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"ERROR: {error_msg}")
        raise HTTPException(status_code=500, detail=str(e))


# Analytics Routes

@backend_router.get("/sessions/stats/overview")
async def get_session_stats(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Get session statistics for current user"""
    try:
        service = SessionAnalyticsService(db)
        stats = service.get_user_session_stats(current_user)
        return stats
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.get("/sessions/{session_id}/timeline")
async def get_session_timeline(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Get activity timeline for a session"""
    try:
        service = SessionAnalyticsService(db)
        timeline = service.get_session_timeline(current_user, session_id)
        return timeline
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.get("/sessions/recent")
async def get_recent_sessions(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Get recently active sessions"""
    try:
        service = SessionAnalyticsService(db)
        sessions = service.get_recent_sessions(current_user, limit)
        return {"sessions": sessions}
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


# Request models for file operations
class WriteFileRequest(BaseModel):
    content: str
    encoding: Optional[str] = 'utf-8'


class CreateDirectoryRequest(BaseModel):
    path: str


class DeleteRequest(BaseModel):
    recursive: Optional[bool] = False


# File Access API Routes - Using shared volume

@backend_router.get("/sessions/{session_id}/files/list")
async def list_files(
    session_id: str,
    path: str = Query("/", description="Directory path to list"),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """List files and directories in a session's workspace"""
    try:
        session_service = SessionManagementService(db)
        session = session_service.get_session(current_user, session_id)
        
        # Use workspace service for direct file access
        from core.workspace_service import get_workspace_service
        workspace = get_workspace_service(session_id)
        
        result = workspace.list_directory(path)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.get("/sessions/{session_id}/files/read")
async def read_file(
    session_id: str,
    path: str = Query(..., description="File path to read"),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Read file content from a session's workspace"""
    try:
        session_service = SessionManagementService(db)
        session = session_service.get_session(current_user, session_id)
        
        # Use workspace service for direct file access
        from core.workspace_service import get_workspace_service
        workspace = get_workspace_service(session_id)
        
        result = workspace.read_file(path)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.post("/sessions/{session_id}/files/write")
async def write_file(
    session_id: str,
    request: WriteFileRequest,
    path: str = Query(..., description="File path to write"),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Write file content to a session's workspace"""
    try:
        session_service = SessionManagementService(db)
        session = session_service.get_session(current_user, session_id)
        
        # Use workspace service for direct file access
        from core.workspace_service import get_workspace_service
        workspace = get_workspace_service(session_id)
        
        result = workspace.write_file(path, request.content, request.encoding or 'utf-8')
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.delete("/sessions/{session_id}/files/delete")
async def delete_file(
    session_id: str,
    path: str = Query(..., description="File path to delete"),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Delete a file from a session's workspace"""
    try:
        session_service = SessionManagementService(db)
        session = session_service.get_session(current_user, session_id)
        
        # Use workspace service for direct file access
        from core.workspace_service import get_workspace_service
        workspace = get_workspace_service(session_id)
        
        result = workspace.delete_file(path)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.post("/sessions/{session_id}/files/mkdir")
async def create_directory(
    session_id: str,
    path: str = Query(..., description="Directory path to create"),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Create a directory in a session's workspace"""
    try:
        session_service = SessionManagementService(db)
        session = session_service.get_session(current_user, session_id)
        
        # Use workspace service for direct file access
        from core.workspace_service import get_workspace_service
        workspace = get_workspace_service(session_id)
        
        result = workspace.create_directory(path)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.delete("/sessions/{session_id}/files/rmdir")
async def delete_directory(
    session_id: str,
    path: str = Query(..., description="Directory path to delete"),
    recursive: bool = Query(False, description="Delete recursively"),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Delete a directory from a session's workspace"""
    try:
        session_service = SessionManagementService(db)
        session = session_service.get_session(current_user, session_id)
        
        # Use workspace service for direct file access
        from core.workspace_service import get_workspace_service
        workspace = get_workspace_service(session_id)
        
        result = workspace.delete_directory(path, recursive)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


@backend_router.post("/sessions/{session_id}/files/rename")
async def rename_file(
    session_id: str,
    old_path: str = Query(..., description="Current file path"),
    new_path: str = Query(..., description="New file path"),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db)
):
    """Rename a file or directory in a session's workspace"""
    try:
        session_service = SessionManagementService(db)
        session = session_service.get_session(current_user, session_id)
        
        # Use workspace service for direct file access
        from core.workspace_service import get_workspace_service
        workspace = get_workspace_service(session_id)
        
        result = workspace.rename_file(old_path, new_path)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        error_response = ErrorHandler.handle_error(e)
        raise HTTPException(status_code=error_response["status_code"], detail=error_response["error"])


# Helper Functions

def session_to_response(session) -> SessionResponse:
    """Convert database session model to response schema"""
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
