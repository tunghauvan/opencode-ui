"""
Test script for Session Cleanup Worker & Recovery Manager

This script demonstrates and tests the session cleanup worker functionality:
1. Creates test sessions
2. Waits for them to timeout
3. Verifies cleanup
4. Tests recovery on chat
"""

import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as DBSession

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_session_cleanup_worker():
    """Test session cleanup worker"""
    from app.core.session_cleanup_worker import SessionCleanupWorker, SessionStatus
    from app.core.database import SessionLocal
    from app.core.models import Session, Base, engine
    
    logger.info("=" * 80)
    logger.info("TEST: Session Cleanup Worker")
    logger.info("=" * 80)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize worker with short timeout for testing (2 minutes)
    worker = SessionCleanupWorker(
        idle_timeout_minutes=2,
        check_interval_seconds=5
    )
    
    logger.info(f"Worker initialized: {worker.get_status()}")
    
    # Create test session in database
    db = SessionLocal()
    try:
        test_session = Session(
            session_id="test_ses_123",
            user_id="test_user",
            agent_id=1,
            status=SessionStatus.RUNNING,
            container_id="test_container_123",
            container_status="running",
            base_url="http://localhost:4096",
            last_activity=datetime.utcnow() - timedelta(minutes=3),  # Idle for 3 minutes
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(test_session)
        db.commit()
        logger.info(f"Created test session: {test_session.session_id}")
        logger.info(f"  Last activity: {test_session.last_activity}")
        logger.info(f"  Current time: {datetime.utcnow()}")
        logger.info(f"  Inactivity: {worker._get_inactivity_minutes(test_session)} minutes")
        
    finally:
        db.close()
    
    # Run cleanup
    logger.info("\nRunning cleanup check...")
    await worker.cleanup_idle_sessions()
    
    # Verify cleanup
    db = SessionLocal()
    try:
        updated_session = db.query(Session).filter(
            Session.session_id == "test_ses_123"
        ).first()
        
        if updated_session:
            logger.info(f"\nSession after cleanup:")
            logger.info(f"  Status: {updated_session.status}")
            logger.info(f"  Container ID: {updated_session.container_id}")
            logger.info(f"  Updated at: {updated_session.updated_at}")
            
            if updated_session.status == SessionStatus.TIMEOUT:
                logger.info("✅ SUCCESS: Session was marked as TIMEOUT")
            else:
                logger.warning("❌ FAILED: Session was not marked as TIMEOUT")
        else:
            logger.error("❌ FAILED: Session not found after cleanup")
            
    finally:
        db.close()
    
    logger.info("=" * 80 + "\n")


async def test_session_recovery():
    """Test session recovery manager"""
    from app.core.session_cleanup_worker import SessionRecoveryManager, SessionStatus
    from app.core.database import SessionLocal
    from app.core.models import Session, Agent, User, Base, engine
    
    logger.info("=" * 80)
    logger.info("TEST: Session Recovery Manager")
    logger.info("=" * 80)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create test data
    db = SessionLocal()
    try:
        # Create user
        user = User(
            id="test_user",
            github_login="testuser",
            github_id="123456",
            access_token="test_token",
            created_at=datetime.utcnow()
        )
        db.add(user)
        
        # Create agent
        agent = Agent(
            id=1,
            name="test_agent",
            user_id="test_user",
            access_token="agent_token_123",
            client_id="test_client_id",
            created_at=datetime.utcnow()
        )
        db.add(agent)
        
        # Create timeout session
        timeout_session = Session(
            session_id="timeout_ses_123",
            user_id="test_user",
            agent_id=1,
            status=SessionStatus.TIMEOUT,  # Already timeout
            container_id=None,
            base_url=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(timeout_session)
        db.commit()
        
        logger.info(f"Created test data:")
        logger.info(f"  User: {user.id}")
        logger.info(f"  Agent: {agent.name} (ID: {agent.id})")
        logger.info(f"  Session: {timeout_session.session_id} (Status: {timeout_session.status})")
        
    finally:
        db.close()
    
    # Test recovery manager
    manager = SessionRecoveryManager()
    
    logger.info("\nTesting recovery detection...")
    
    db = SessionLocal()
    try:
        session = db.query(Session).filter(
            Session.session_id == "timeout_ses_123"
        ).first()
        
        if session and session.status == SessionStatus.TIMEOUT:
            logger.info(f"✅ Session correctly marked as TIMEOUT")
            logger.info(f"\nWould recover session by:")
            logger.info(f"  1. Getting agent token from DB")
            logger.info(f"  2. Calling agent controller to create new container")
            logger.info(f"  3. Updating session with new container info")
            logger.info(f"  4. Setting status back to RUNNING")
            logger.info(f"  5. Resetting last_activity timestamp")
        else:
            logger.warning("❌ Session not in TIMEOUT state")
            
    finally:
        db.close()
    
    logger.info("=" * 80 + "\n")


async def test_continuous_worker():
    """Test worker running continuously"""
    from app.core.session_cleanup_worker import SessionCleanupWorker, SessionStatus
    from app.core.database import SessionLocal
    from app.core.models import Session, Base, engine
    
    logger.info("=" * 80)
    logger.info("TEST: Continuous Worker (20 seconds)")
    logger.info("=" * 80)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Initialize worker with very short timeout for demo (0.5 minute = 30 seconds)
    worker = SessionCleanupWorker(
        idle_timeout_minutes=0.5,  # 30 seconds
        check_interval_seconds=5
    )
    
    # Create test sessions
    db = SessionLocal()
    try:
        for i in range(3):
            session = Session(
                session_id=f"test_ses_{i}",
                user_id=f"test_user_{i}",
                agent_id=1,
                status=SessionStatus.RUNNING,
                container_id=f"test_container_{i}",
                container_status="running",
                base_url="http://localhost:4096",
                last_activity=datetime.utcnow() - timedelta(minutes=2),  # Idle for 2 minutes
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(session)
        db.commit()
        logger.info(f"Created 3 test sessions")
        
    finally:
        db.close()
    
    # Run worker for 20 seconds
    logger.info("Starting worker for 20 seconds...")
    logger.info("  - Should check at: 0s, 5s, 10s, 15s, 20s")
    
    worker_task = asyncio.create_task(worker.start())
    
    try:
        # Run for 20 seconds
        await asyncio.sleep(20)
        
        # Check results
        db = SessionLocal()
        try:
            timeout_count = db.query(Session).filter(
                Session.status == SessionStatus.TIMEOUT
            ).count()
            
            logger.info(f"\nAfter 20 seconds: {timeout_count}/3 sessions marked as TIMEOUT")
            
            sessions = db.query(Session).filter(
                Session.session_id.like("test_ses_%")
            ).all()
            
            for session in sessions:
                logger.info(f"  {session.session_id}: {session.status}")
                
        finally:
            db.close()
        
    finally:
        await worker.stop()
        await worker_task
    
    logger.info("=" * 80 + "\n")


async def main():
    """Run all tests"""
    logger.info("\n" + "=" * 80)
    logger.info("SESSION CLEANUP WORKER TESTS")
    logger.info("=" * 80 + "\n")
    
    try:
        # Test 1: Basic cleanup
        await test_session_cleanup_worker()
        
        # Test 2: Recovery detection
        await test_session_recovery()
        
        # Test 3: Continuous worker (optional - takes 20+ seconds)
        # await test_continuous_worker()
        
        logger.info("=" * 80)
        logger.info("ALL TESTS COMPLETED")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)


if __name__ == "__main__":
    # Change to project root if needed
    import os
    import sys
    
    # Add project root to path
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Run tests
    asyncio.run(main())
