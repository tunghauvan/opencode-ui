"""
Session Cleanup Worker - Background task to cleanup idle sessions
Removes containers và marks sessions as terminated after inactivity timeout
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session as DBSession

from app.core.database import get_db, SessionLocal
from app.core.models import Session
from app.core.docker_ops import DockerOps

logger = logging.getLogger(__name__)


class SessionStatus:
    """Session status constants"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    TERMINATED = "terminated"
    TIMEOUT = "timeout"


class SessionCleanupWorker:
    """
    Background worker to cleanup idle sessions
    
    Features:
    - Runs periodically (configurable interval)
    - Removes containers for idle sessions
    - Marks sessions as TIMEOUT status
    - Keeps session data for history
    - Logs all cleanup operations
    """
    
    def __init__(
        self,
        idle_timeout_minutes: int = 15,
        check_interval_seconds: int = 60,
        db_session: Optional[DBSession] = None
    ):
        """
        Initialize cleanup worker
        
        Args:
            idle_timeout_minutes: Minutes of inactivity before cleanup (default 15)
            check_interval_seconds: How often to check for idle sessions (default 60)
            db_session: SQLAlchemy session (if None, will create new for each check)
        """
        self.idle_timeout_minutes = idle_timeout_minutes
        self.check_interval_seconds = check_interval_seconds
        self.db_session = db_session
        self.running = False
        self.docker_ops = DockerOps()
        
    async def start(self):
        """Start the cleanup worker"""
        self.running = True
        logger.info(
            "SessionCleanupWorker started",
            idle_timeout_minutes=self.idle_timeout_minutes,
            check_interval_seconds=self.check_interval_seconds
        )
        
        try:
            while self.running:
                await self.cleanup_idle_sessions()
                await asyncio.sleep(self.check_interval_seconds)
        except Exception as e:
            logger.error(f"SessionCleanupWorker crashed: {e}", exc_info=True)
            self.running = False
            raise
            
    async def stop(self):
        """Stop the cleanup worker"""
        self.running = False
        logger.info("SessionCleanupWorker stopped")
        
    async def cleanup_idle_sessions(self):
        """Find and cleanup idle sessions"""
        try:
            # Get database session
            db = self.db_session or SessionLocal()
            
            try:
                # Calculate timeout threshold
                timeout_threshold = datetime.utcnow() - timedelta(
                    minutes=self.idle_timeout_minutes
                )
                
                # Find idle sessions that are still running
                idle_sessions = db.query(Session).filter(
                    Session.status == SessionStatus.RUNNING,
                    Session.last_activity < timeout_threshold
                ).all()
                
                if idle_sessions:
                    logger.info(
                        f"Found {len(idle_sessions)} idle sessions to cleanup",
                        timeout_threshold=timeout_threshold.isoformat()
                    )
                
                for session in idle_sessions:
                    await self._cleanup_single_session(session, db)
                    
            finally:
                if not self.db_session:  # Only close if we created it
                    db.close()
                    
        except Exception as e:
            logger.error(f"Error in cleanup_idle_sessions: {e}", exc_info=True)
            
    async def _cleanup_single_session(self, session: Session, db: DBSession):
        """
        Cleanup a single idle session
        
        Steps:
        1. Stop container (if running)
        2. Mark session as TIMEOUT
        3. Update timestamp
        4. Log the cleanup
        """
        session_id = session.session_id
        
        try:
            logger.info(
                "Cleaning up idle session",
                session_id=session_id,
                user_id=session.user_id,
                inactivity_minutes=self._get_inactivity_minutes(session)
            )
            
            # Stop container if it exists
            if session.container_id:
                try:
                    await self._stop_container_safely(session.container_id)
                    logger.info(
                        "Container stopped",
                        session_id=session_id,
                        container_id=session.container_id
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to stop container {session.container_id}: {e}",
                        session_id=session_id
                    )
            
            # Update session status
            session.status = SessionStatus.TIMEOUT
            session.container_id = None
            session.container_status = None
            session.updated_at = datetime.utcnow()
            
            db.add(session)
            db.commit()
            
            logger.info(
                "Session cleaned up successfully",
                session_id=session_id,
                status=SessionStatus.TIMEOUT
            )
            
        except Exception as e:
            db.rollback()
            logger.error(
                f"Failed to cleanup session {session_id}: {e}",
                exc_info=True
            )
            
    async def _stop_container_safely(self, container_id: str):
        """
        Safely stop a container with timeout
        
        Args:
            container_id: Docker container ID
            
        Raises:
            Exception if container stop fails
        """
        try:
            # Try graceful shutdown first (10s timeout)
            self.docker_ops.stop_container(container_id, timeout=10)
        except Exception as e:
            logger.warning(f"Graceful stop failed, forcing: {e}")
            # Force stop if graceful failed
            try:
                self.docker_ops.kill_container(container_id)
            except Exception as force_error:
                logger.error(f"Force stop also failed: {force_error}")
                raise force_error
                
    def _get_inactivity_minutes(self, session: Session) -> int:
        """Calculate how many minutes session has been idle"""
        if not session.last_activity:
            return -1  # Never used
        
        inactivity = datetime.utcnow() - session.last_activity
        return int(inactivity.total_seconds() / 60)
        
    def get_status(self) -> dict:
        """Get worker status"""
        return {
            "running": self.running,
            "idle_timeout_minutes": self.idle_timeout_minutes,
            "check_interval_seconds": self.check_interval_seconds
        }


class SessionRecoveryManager:
    """
    Manager to recover/recreate sessions when user tries to chat
    
    Features:
    - Detects timeout sessions on chat attempt
    - Automatically recreates container
    - Restores session to RUNNING status
    - Logs recovery operations
    """
    
    def __init__(self, db_session: Optional[DBSession] = None):
        """
        Initialize recovery manager
        
        Args:
            db_session: SQLAlchemy session (if None, will create new for each operation)
        """
        self.db_session = db_session
        self.docker_ops = DockerOps()
        
    async def get_or_recover_session(self, session_id: str, user_id: str) -> Session:
        """
        Get session, and recover if it was timeout
        
        Args:
            session_id: Session ID to get/recover
            user_id: User ID for authorization check
            
        Returns:
            Session object (recovered or running)
            
        Raises:
            ValueError if session not found or user not authorized
        """
        db = self.db_session or SessionLocal()
        
        try:
            # Get session with authorization check
            session = db.query(Session).filter(
                Session.session_id == session_id,
                Session.user_id == user_id
            ).first()
            
            if not session:
                raise ValueError(f"Session {session_id} not found")
            
            # If session is timeout, recover it
            if session.status == SessionStatus.TIMEOUT:
                logger.info(
                    "Recovering timeout session",
                    session_id=session_id,
                    user_id=user_id
                )
                await self._recover_session(session, db)
                
            return session
            
        finally:
            if not self.db_session:  # Only close if we created it
                db.close()
                
    async def _recover_session(self, session: Session, db: DBSession):
        """
        Recover a timeout session by recreating its container
        
        Steps:
        1. Get agent information
        2. Create new container
        3. Update session with new container info
        4. Mark session as RUNNING
        """
        try:
            logger.info(
                "Starting session recovery",
                session_id=session.session_id,
                agent_id=session.agent_id
            )
            
            # Get agent to retrieve access token
            from app.core.models import Agent
            agent = db.query(Agent).filter(Agent.id == session.agent_id).first()
            
            if not agent:
                raise ValueError(f"Agent {session.agent_id} not found")
            
            # Create new container for this session
            # Using same format as agent controller
            container_info = await self._create_session_container(
                session.session_id,
                agent.access_token
            )
            
            # Update session with new container info
            session.container_id = container_info["container_id"]
            session.container_status = container_info.get("container_status", "running")
            session.base_url = container_info.get("base_url")
            session.status = SessionStatus.RUNNING
            session.updated_at = datetime.utcnow()
            session.last_activity = datetime.utcnow()  # Reset activity timestamp
            
            db.add(session)
            db.commit()
            
            logger.info(
                "Session recovered successfully",
                session_id=session.session_id,
                new_container_id=container_info["container_id"]
            )
            
        except Exception as e:
            db.rollback()
            logger.error(
                f"Failed to recover session {session.session_id}: {e}",
                exc_info=True
            )
            raise
            
    async def _create_session_container(
        self,
        session_id: str,
        agent_token: str
    ) -> dict:
        """
        Create a container for the session
        
        Args:
            session_id: Session ID
            agent_token: Agent access token
            
        Returns:
            Dict with container_id, container_status, base_url
        """
        # Call agent controller to create container
        import httpx
        import os
        
        agent_controller_url = os.getenv(
            "AGENT_CONTROLLER_URL",
            "http://localhost:8001"
        )
        service_secret = os.getenv(
            "AGENT_SERVICE_SECRET",
            "default-secret-change-in-production"
        )
        
        try:
            response = httpx.post(
                f"{agent_controller_url}/sessions/agent",
                json={
                    "session_id": session_id,
                    "agent_token": agent_token,
                },
                headers={"X-Service-Secret": service_secret},
                timeout=60.0
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"Failed to create container: {e}")
            raise
            
    def get_status(self) -> dict:
        """Get recovery manager status"""
        return {
            "type": "SessionRecoveryManager",
            "ready": True
        }
