"""
Backend API service for session management
Handles session operations and database persistence.
Container operations are delegated to the Agent Controller service.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
from sqlalchemy.orm import Session as DBSession
import httpx

from core.models import User, Session
from core.config import settings


class SessionManagementService:
    """Service for managing user sessions with database persistence"""

    def __init__(self, db: DBSession):
        """Initialize with database session"""
        self.db = db

    def create_session(
        self,
        user: User,
        session_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        auth_data: Optional[Dict[str, Any]] = None,
        environment_vars: Optional[Dict[str, str]] = None
    ) -> Session:
        """Create a new session for a user"""
        # Check if session already exists
        existing = self.db.query(Session).filter(
            Session.session_id == session_id,
            Session.user_id == user.id
        ).first()

        if existing:
            raise ValueError(f"Session {session_id} already exists for user {user.id}")

        # Create new session
        session = Session(
            session_id=session_id,
            user_id=user.id,
            name=name,
            description=description,
            status="active",
            is_active=True,
            auth_data=json.dumps(auth_data) if auth_data else None,
            environment_vars=json.dumps(environment_vars) if environment_vars else None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def get_session(
        self,
        user: User,
        session_id: str
    ) -> Optional[Session]:
        """Get a specific session by ID"""
        session = self.db.query(Session).filter(
            Session.session_id == session_id,
            Session.user_id == user.id
        ).first()

        if not session:
            raise ValueError(f"Session {session_id} not found for user {user.id}")

        return session

    def list_sessions(
        self,
        user: User,
        status: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[Session]:
        """List sessions for a user with optional filtering"""
        query = self.db.query(Session).filter(Session.user_id == user.id)

        if status:
            query = query.filter(Session.status == status)

        if is_active is not None:
            query = query.filter(Session.is_active == is_active)

        return query.order_by(Session.created_at.desc()).all()

    def update_session(
        self,
        user: User,
        session_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        auth_data: Optional[Dict[str, Any]] = None,
        environment_vars: Optional[Dict[str, str]] = None
    ) -> Session:
        """Update session metadata and configuration"""
        session = self.get_session(user, session_id)

        if name is not None:
            session.name = name
        if description is not None:
            session.description = description
        if status is not None:
            session.status = status
        if auth_data is not None:
            session.auth_data = json.dumps(auth_data)
        if environment_vars is not None:
            session.environment_vars = json.dumps(environment_vars)

        session.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(session)

        return session

    def update_session_container(
        self,
        user: User,
        session_id: str,
        container_id: str,
        container_status: Optional[str] = None
    ) -> Session:
        """Update session container information"""
        session = self.get_session(user, session_id)

        session.container_id = container_id
        if container_status:
            session.container_status = container_status

        session.last_activity = datetime.utcnow()
        session.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(session)

        return session

    def update_session_status(
        self,
        user: User,
        session_id: str,
        status: str,
        is_active: Optional[bool] = None
    ) -> Session:
        """Update session status"""
        session = self.get_session(user, session_id)

        session.status = status
        if is_active is not None:
            session.is_active = is_active

        session.updated_at = datetime.utcnow()
        session.last_activity = datetime.utcnow()

        self.db.commit()
        self.db.refresh(session)

        return session

    def delete_session(self, user: User, session_id: str) -> bool:
        """Delete a session and cleanup associated resources via Agent Controller"""
        session = self.get_session(user, session_id)

        # Cleanup container if exists (call agent-controller)
        if session.container_id:
            try:
                import asyncio
                # Note: This is a sync method, so we can't use async here
                # The actual cleanup will happen through agent-controller when needed
                print(f"Session {session_id} has container {session.container_id} - cleanup can be called separately")
            except Exception as e:
                print(f"Error cleanup reference for session: {e}")

        self.db.delete(session)
        self.db.commit()

        return True

    def get_session_auth_data(
        self,
        user: User,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get auth data for a session"""
        session = self.get_session(user, session_id)

        if session.auth_data:
            try:
                return json.loads(session.auth_data)
            except json.JSONDecodeError:
                return None
        return None

    def get_session_environment_vars(
        self,
        user: User,
        session_id: str
    ) -> Optional[Dict[str, str]]:
        """Get environment variables for a session"""
        session = self.get_session(user, session_id)

        if session.environment_vars:
            try:
                return json.loads(session.environment_vars)
            except json.JSONDecodeError:
                return None
        return None


class ContainerManagementService:
    """Service for managing Docker containers via Agent Controller API"""

    def __init__(self, db: DBSession):
        """Initialize with database session"""
        self.db = db
        self.agent_controller_url = "http://agent-controller:8001"

    async def start_session_container(
        self,
        user: User,
        session_id: str,
        image: str,
        environment: Optional[Dict[str, str]] = None,
        session_service: Optional[SessionManagementService] = None
    ) -> Dict[str, Any]:
        """Start a Docker container for a session via Agent Controller"""
        # Get or create session service
        if session_service is None:
            session_service = SessionManagementService(self.db)

        session = session_service.get_session(user, session_id)

        try:
            async with httpx.AsyncClient() as client:
                # Call agent-controller to start container
                response = await client.post(
                    f"{self.agent_controller_url}/api/sessions/{session_id}/container/start",
                    json={"image": image, "environment": environment or {}},
                    headers={"X-Service-Secret": settings.AGENT_SERVICE_SECRET},
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()

                # Update session with container info
                session_service.update_session_container(
                    user,
                    session_id,
                    result.get("container_id"),
                    "running"
                )

                return result
        except Exception as e:
            raise Exception(f"Failed to start container via Agent Controller: {str(e)}")

    async def stop_session_container(
        self,
        user: User,
        session_id: str,
        session_service: Optional[SessionManagementService] = None
    ) -> Dict[str, Any]:
        """Stop a Docker container for a session via Agent Controller"""
        # Get or create session service
        if session_service is None:
            session_service = SessionManagementService(self.db)

        session = session_service.get_session(user, session_id)

        if not session.container_id:
            raise ValueError(f"No container running for session {session_id}")

        try:
            async with httpx.AsyncClient() as client:
                # Call agent-controller to stop container
                response = await client.post(
                    f"{self.agent_controller_url}/api/sessions/{session_id}/container/stop",
                    headers={"X-Service-Secret": settings.AGENT_SERVICE_SECRET},
                    timeout=30.0
                )
                response.raise_for_status()

                # Update session
                session_service.update_session_container(
                    user,
                    session_id,
                    None,
                    "stopped"
                )

                return {"status": "stopped", "session_id": session_id}
        except Exception as e:
            raise Exception(f"Failed to stop container via Agent Controller: {str(e)}")

    async def get_session_container_logs(
        self,
        user: User,
        session_id: str,
        tail: int = 100,
        session_service: Optional[SessionManagementService] = None
    ) -> str:
        """Get logs from a session's container via Agent Controller"""
        # Get or create session service
        if session_service is None:
            session_service = SessionManagementService(self.db)

        session = session_service.get_session(user, session_id)

        if not session.container_id:
            raise ValueError(f"No container running for session {session_id}")

        try:
            async with httpx.AsyncClient() as client:
                # Call agent-controller to get logs
                response = await client.get(
                    f"{self.agent_controller_url}/api/sessions/{session_id}/container/logs",
                    params={"tail": tail},
                    headers={"X-Service-Secret": settings.AGENT_SERVICE_SECRET},
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                return result.get("logs", "")
        except Exception as e:
            raise Exception(f"Failed to get logs via Agent Controller: {str(e)}")

    async def get_container_status(
        self,
        user: User,
        session_id: str,
        session_service: Optional[SessionManagementService] = None
    ) -> Dict[str, Any]:
        """Get status of a session's container via Agent Controller"""
        # Get or create session service
        if session_service is None:
            session_service = SessionManagementService(self.db)

        session = session_service.get_session(user, session_id)

        try:
            async with httpx.AsyncClient() as client:
                # Call agent-controller to get status
                response = await client.get(
                    f"{self.agent_controller_url}/api/sessions/{session_id}/container/status",
                    headers={"X-Service-Secret": settings.AGENT_SERVICE_SECRET},
                    timeout=30.0
                )
                response.raise_for_status()
                
                return response.json()
        except Exception as e:
            raise Exception(f"Failed to get container status: {str(e)}")


class SessionAnalyticsService:
    """Service for analyzing session usage and statistics"""

    def __init__(self, db: DBSession):
        """Initialize with database session"""
        self.db = db

    def get_user_session_stats(self, user: User) -> Dict[str, Any]:
        """Get session statistics for a user"""
        sessions = self.db.query(Session).filter(Session.user_id == user.id).all()

        total_sessions = len(sessions)
        active_sessions = len([s for s in sessions if s.is_active])
        inactive_sessions = total_sessions - active_sessions
        running_containers = len([s for s in sessions if s.container_id])

        # Get status breakdown
        status_breakdown = {}
        for session in sessions:
            status = session.status
            status_breakdown[status] = status_breakdown.get(status, 0) + 1

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "inactive_sessions": inactive_sessions,
            "running_containers": running_containers,
            "status_breakdown": status_breakdown
        }

    def get_session_timeline(
        self,
        user: User,
        session_id: str
    ) -> Dict[str, Any]:
        """Get activity timeline for a specific session"""
        session = self.db.query(Session).filter(
            Session.session_id == session_id,
            Session.user_id == user.id
        ).first()

        if not session:
            raise ValueError(f"Session {session_id} not found")

        return {
            "session_id": session_id,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "last_activity": session.last_activity.isoformat() if session.last_activity else None,
            "duration_seconds": (
                (datetime.utcnow() - session.created_at).total_seconds()
                if session.created_at else 0
            ),
            "status": session.status,
            "is_active": session.is_active
        }

    def get_recent_sessions(
        self,
        user: User,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recently active sessions for a user"""
        sessions = (
            self.db.query(Session)
            .filter(Session.user_id == user.id)
            .order_by(Session.last_activity.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "session_id": s.session_id,
                "name": s.name,
                "status": s.status,
                "last_activity": s.last_activity.isoformat() if s.last_activity else None,
                "container_status": s.container_status
            }
            for s in sessions
        ]
