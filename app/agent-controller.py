#!/usr/bin/env python3
"""
OpenCode Agent Controller API
FastAPI service for managing Docker containers and sessions
"""

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import docker

from .core.config import settings
from .core.docker_ops import (
    ensure_volume_exists,
    create_session_folder,
    get_session_auth_data,
    update_session_auth_data,
    remove_session_folder,
    cleanup_container,
    run_session_container as run_container_in_docker,
    get_container_logs
)
from .core.database import init_db
from .core.session_ops import (
    create_session as create_session_in_db,
    get_session as get_session_from_db,
    update_session_auth as update_session_auth_in_db,
    update_session_container as update_session_container_in_db,
    stop_session_container as stop_session_container_in_db,
    list_sessions as list_sessions_from_db,
    delete_session as delete_session_from_db,
    session_exists
)

# Configuration
DEFAULT_IMAGE = "opencode-ui-opencode-agent:latest"

# Docker client
docker_client = docker.from_env()

# Authentication dependency
async def verify_service_secret(x_service_secret: str = Header(..., alias="X-Service-Secret")):
    """Verify the service secret for authentication"""
    if x_service_secret != settings.AGENT_SERVICE_SECRET:
        raise HTTPException(
            status_code=401,
            detail="Invalid service secret",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return x_service_secret

app = FastAPI(
    title="OpenCode Agent Controller",
    description="API for managing OpenCode agent sessions and containers",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class SessionCreateRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    github_token: Optional[str] = Field(None, description="GitHub OAuth token")

class AgentSessionCreateRequest(BaseModel):
    session_id: str = Field(..., description="Unique session identifier")
    agent_id: int = Field(..., description="Agent ID")
    agent_token: str = Field(..., description="GitHub OAuth token for agent")
    title: Optional[str] = Field(None, description="Session title")

class AuthData(BaseModel):
    github_copilot: Optional[Dict[str, Any]] = Field(None, description="GitHub Copilot auth configuration")

class SessionResponse(BaseModel):
    session_id: str
    created_at: str
    auth_data: Optional[AuthData] = None
    container_status: Optional[str] = None
    container_id: Optional[str] = None

class ContainerRunRequest(BaseModel):
    image: str = Field(DEFAULT_IMAGE, description="Docker image to run")
    environment: Optional[Dict[str, str]] = Field({}, description="Environment variables")
    is_agent: bool = Field(False, description="Whether this is an agent container")

class SessionListResponse(BaseModel):
    sessions: List[Dict[str, Any]]

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    ensure_volume_exists()
    init_db()  # Initialize database tables

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/sessions", response_model=SessionResponse, dependencies=[Depends(verify_service_secret)])
async def create_session(request: SessionCreateRequest):
    """Create a new session"""
    try:
        # Create session in storage
        session_data = create_session_in_db(request.session_id, request.github_token)

        # Create session folder and auth.json
        auth_data = create_session_folder(request.session_id, request.github_token)

        # Update session with auth data
        update_session_auth_in_db(request.session_id, auth_data)

        # Get updated session data
        session_data = get_session_from_db(request.session_id)

        return SessionResponse(**session_data)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@app.post("/sessions/agent", dependencies=[Depends(verify_service_secret)])
async def create_agent_session(request: AgentSessionCreateRequest):
    """Create a new agent-based session with dedicated container"""
    try:
        print(f"Creating agent session: {request.session_id}, agent: {request.agent_id}")
        
        # Create session in storage
        session_data = create_session_in_db(request.session_id, request.agent_token)
        print(f"Created session in DB: {session_data}")

        # Create session folder and auth.json with agent token
        auth_data = create_session_folder(request.session_id, request.agent_token)
        print(f"Created session folder with auth data: {auth_data}")

        # Update session with auth data
        update_session_auth_in_db(request.session_id, auth_data)
        print("Updated session auth data")

        # Run agent container with opencode serve
        print(f"Running container with image: {DEFAULT_IMAGE}")
        container_id = run_container_in_docker(
            session_id=request.session_id,
            image=DEFAULT_IMAGE,
            environment={},
            agent_token=request.agent_token,
            is_agent=True
        )
        print(f"Container started: {container_id}")

        # Get the actual port that Docker assigned
        container = docker_client.containers.get(container_id)
        ports = container.attrs['NetworkSettings']['Ports']
        container_port = ports.get('4096/tcp', [{}])[0].get('HostPort')
        if not container_port:
            print("Warning: Could not determine container port")
            container_port = "4096"  # Fallback
        
        print(f"Container running on port: {container_port}")
        
        # Wait for container to be ready and create OpenCode session
        import time
        import httpx
        base_url = f"http://localhost:{container_port}"
        
        # Wait up to 30 seconds for container to be ready
        for i in range(30):
            try:
                response = httpx.get(f"{base_url}/health", timeout=5.0)
                if response.status_code == 200:
                    print("Agent container is ready")
                    break
            except:
                pass
            time.sleep(1)
        else:
            print("Warning: Agent container did not respond to health check")
        
        # Try to create a session in the OpenCode agent
        opencode_session_id = None
        try:
            response = httpx.post(f"{base_url}/session", json={"title": request.title or f"Agent Session {request.session_id[:8]}"}, timeout=10.0)
            if response.status_code == 200:
                session_data = response.json()
                opencode_session_id = session_data.get("id")
                print(f"Created OpenCode session: {opencode_session_id}")
        except Exception as e:
            print(f"Warning: Could not create OpenCode session: {e}")

        # Update session with container info and OpenCode session ID
        update_session_container_in_db(request.session_id, container_id, "running", opencode_session_id)
        print("Updated session with container info")

        # Construct base_url for agent container using Docker DNS
        base_url = f"http://agent_{request.session_id}:4096"

        return {
            "session_id": request.session_id,
            "agent_id": request.agent_id,
            "container_id": container_id,
            "container_status": "running",
            "base_url": base_url,
            "created_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        import traceback
        print(f"Error creating agent session: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Failed to create agent session: {str(e)}")

@app.get("/sessions", response_model=SessionListResponse, dependencies=[Depends(verify_service_secret)])
async def list_sessions():
    """List all sessions"""
    sessions = list_sessions_from_db()
    return SessionListResponse(sessions=sessions)

@app.get("/sessions/{session_id}", response_model=SessionResponse, dependencies=[Depends(verify_service_secret)])
async def get_session(session_id: str):
    """Get session information"""
    try:
        # Get session data
        session_data = get_session_from_db(session_id)

        # Refresh auth data from volume
        auth_data = get_session_auth_data(session_id)
        if auth_data:
            update_session_auth_in_db(session_id, auth_data)
            session_data = get_session_from_db(session_id)

        return SessionResponse(**session_data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.put("/sessions/{session_id}/auth", dependencies=[Depends(verify_service_secret)])
async def update_session_auth(session_id: str, auth_data: AuthData):
    """Update session auth.json"""
    try:
        # Update auth data in volume
        update_session_auth_data(session_id, auth_data.model_dump())

        # Update session storage
        update_session_auth_in_db(session_id, auth_data.model_dump())

        return {"status": "updated", "session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update auth: {str(e)}")

@app.delete("/sessions/{session_id}", dependencies=[Depends(verify_service_secret)])
async def delete_session(session_id: str, background_tasks: BackgroundTasks):
    """Delete session and cleanup"""
    try:
        session_data = get_session_from_db(session_id)

        # Stop container if running
        if session_data.get("container_id"):
            background_tasks.add_task(cleanup_container, session_data["container_id"])

        # Remove session folder from volume
        remove_session_folder(session_id)

        # Remove from storage
        delete_session_from_db(session_id)

        return {"status": "deleted", "session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/sessions/{session_id}/run", dependencies=[Depends(verify_service_secret)])
async def run_session_container(session_id: str, request: ContainerRunRequest, background_tasks: BackgroundTasks):
    """Run container for session"""
    try:
        session_data = get_session_from_db(session_id)

        # Stop existing container if any
        if session_data.get("container_id"):
            background_tasks.add_task(cleanup_container, session_data["container_id"])

        # Run container
        container_id = run_container_in_docker(session_id, request.image, request.environment or {}, is_agent=request.is_agent)

        # Update session data
        update_session_container_in_db(session_id, container_id, "running")

        return {
            "container_id": container_id,
            "status": "running",
            "session_id": session_id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run container: {str(e)}")

@app.post("/sessions/{session_id}/stop", dependencies=[Depends(verify_service_secret)])
async def stop_session_container(session_id: str, background_tasks: BackgroundTasks):
    """Stop session container"""
    try:
        session_data = get_session_from_db(session_id)
        container_id = session_data.get("container_id")

        if not container_id:
            raise HTTPException(status_code=404, detail="No container running for session")

        background_tasks.add_task(cleanup_container, container_id)

        # Update status
        stop_session_container_in_db(session_id)

        return {"status": "stopping", "session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/sessions/{session_id}/logs", dependencies=[Depends(verify_service_secret)])
async def get_session_logs(session_id: str, tail: int = 100):
    """Get container logs for session"""
    try:
        session_data = get_session_from_db(session_id)
        container_id = session_data.get("container_id")

        if not container_id:
            raise HTTPException(status_code=404, detail="No container running for session")

        logs = get_container_logs(container_id, tail)
        return {"logs": logs, "session_id": session_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get logs: {str(e)}")


@app.get("/sessions/{session_id}/status", dependencies=[Depends(verify_service_secret)])
async def get_session_status(session_id: str):
    """Get session and container status"""
    try:
        session_data = get_session_from_db(session_id)
        
        status_info = {
            "session_id": session_id,
            "session_status": "exists",
            "container_id": session_data.get("container_id"),
            "container_status": session_data.get("container_status", "unknown")
        }
        
        # If we have a container_id, check if it's actually running
        if session_data.get("container_id"):
            try:
                container = docker_client.containers.get(session_data["container_id"])
                status_info["container_status"] = container.status
                status_info["container_running"] = container.status == "running"
            except docker.errors.NotFound:
                status_info["container_status"] = "not_found"
                status_info["container_running"] = False
            except Exception as e:
                status_info["container_error"] = str(e)
        
        return status_info
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)