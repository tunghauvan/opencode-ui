"""
Session management integration for FastAPI app
Handles cleanup worker startup/shutdown and session recovery
"""

import logging
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

from app.core.session_cleanup_worker import (
    SessionCleanupWorker,
    SessionRecoveryManager,
    SessionStatus
)
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# Global instances
cleanup_worker: Optional[SessionCleanupWorker] = None
recovery_manager: Optional[SessionRecoveryManager] = None
cleanup_task: Optional[asyncio.Task] = None


def init_session_management(
    idle_timeout_minutes: int = 15,
    check_interval_seconds: int = 60
):
    """
    Initialize session management services
    
    Should be called on application startup
    
    Args:
        idle_timeout_minutes: Minutes before session cleanup
        check_interval_seconds: How often to check for idle sessions
    """
    global cleanup_worker, recovery_manager
    
    cleanup_worker = SessionCleanupWorker(
        idle_timeout_minutes=idle_timeout_minutes,
        check_interval_seconds=check_interval_seconds
    )
    
    recovery_manager = SessionRecoveryManager()
    
    logger.info(
        "Session management initialized",
        idle_timeout_minutes=idle_timeout_minutes,
        check_interval_seconds=check_interval_seconds
    )


async def start_session_cleanup_worker():
    """
    Start the background cleanup worker
    
    Should be called in FastAPI lifespan startup
    """
    global cleanup_worker, cleanup_task
    
    if cleanup_worker is None:
        logger.error("SessionCleanupWorker not initialized!")
        return
    
    logger.info("Starting SessionCleanupWorker...")
    cleanup_task = asyncio.create_task(cleanup_worker.start())
    logger.info("SessionCleanupWorker started successfully")


async def stop_session_cleanup_worker():
    """
    Stop the background cleanup worker
    
    Should be called in FastAPI lifespan shutdown
    """
    global cleanup_worker, cleanup_task
    
    if cleanup_worker is None:
        return
    
    logger.info("Stopping SessionCleanupWorker...")
    await cleanup_worker.stop()
    
    if cleanup_task:
        try:
            await asyncio.wait_for(cleanup_task, timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("SessionCleanupWorker did not stop gracefully")
            cleanup_task.cancel()
    
    logger.info("SessionCleanupWorker stopped")


async def get_or_recover_session(session_id: str, user_id: str):
    """
    Get session with automatic recovery if timeout
    
    This should be called in chat endpoints instead of direct DB query
    
    Args:
        session_id: Session ID
        user_id: User ID for authorization
        
    Returns:
        Session object (recovered or running)
        
    Raises:
        ValueError if session not found
    """
    global recovery_manager
    
    if recovery_manager is None:
        raise RuntimeError("Session management not initialized")
    
    return await recovery_manager.get_or_recover_session(session_id, user_id)


def get_cleanup_worker_status() -> dict:
    """Get status of cleanup worker"""
    global cleanup_worker
    
    if cleanup_worker is None:
        return {"status": "not_initialized"}
    
    return cleanup_worker.get_status()


def get_recovery_manager_status() -> dict:
    """Get status of recovery manager"""
    global recovery_manager
    
    if recovery_manager is None:
        return {"status": "not_initialized"}
    
    return recovery_manager.get_status()


@asynccontextmanager
async def lifespan_session_management(idle_timeout_minutes: int = 15, check_interval_seconds: int = 60):
    """
    Context manager for session management lifecycle
    
    Usage in main.py:
    ```
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with lifespan_session_management(idle_timeout_minutes=15):
            yield
    
    app = FastAPI(lifespan=lifespan)
    ```
    
    Or with existing lifespan:
    ```
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # ... existing startup code ...
        async with lifespan_session_management(idle_timeout_minutes=15):
            yield
        # ... existing shutdown code ...
    ```
    """
    # Startup
    init_session_management(idle_timeout_minutes, check_interval_seconds)
    await start_session_cleanup_worker()
    
    try:
        yield
    finally:
        # Shutdown
        await stop_session_cleanup_worker()
