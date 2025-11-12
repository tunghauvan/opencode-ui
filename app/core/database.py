"""
Database configuration and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# SQLite database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/db.sqlite3")

# Create engine with appropriate settings for SQLite
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import Base from models
from core.models import Base  # noqa: E402


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session dependency for FastAPI"""
    print("DEBUG: get_db called")
    db = SessionLocal()
    print("DEBUG: SessionLocal created")
    try:
        print("DEBUG: yielding db")
        yield db
    finally:
        print("DEBUG: closing db")
        db.close()
