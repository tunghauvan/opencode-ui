"""
User and GitHub token models
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# Create Base here to avoid circular import
Base = declarative_base()


class User(Base):
    """User model for storing GitHub user information and tokens"""
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)  # GitHub user ID
    github_login = Column(String, unique=True, index=True)
    github_id = Column(String, unique=True, index=True)
    email = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True)
    
    # OAuth tokens
    access_token = Column(String)
    refresh_token = Column(String, nullable=True)  # GitHub refresh token (ghu_xxx)
    token_expires_at = Column(DateTime, nullable=True)
    
    # User info
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Relationship with agents
    agents = relationship("Agent", back_populates="user", cascade="all, delete-orphan")

    # Relationship with sessions
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(github_login={self.github_login}, github_id={self.github_id})>"


class Agent(Base):
    """Agent model for storing AI agent authentication and tokens"""
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)  # Agent name/identifier
    description = Column(String, nullable=True)  # Agent description
    
    # Foreign key to user
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # OAuth tokens for agent
    access_token = Column(String)
    refresh_token = Column(String, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    
    # Agent configuration
    client_id = Column(String, nullable=False)  # GitHub App client ID used
    scopes = Column(String, nullable=True)  # OAuth scopes granted
    
    # Agent status
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to user
    user = relationship("User", back_populates="agents")

    def __repr__(self):
        return f"<Agent(name={self.name}, user_id={self.user_id})>"


class Session(Base):
    """Session model for storing user sessions and their associated data"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, unique=True, index=True, nullable=False)  # Unique session identifier

    # Foreign key to user
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    # Foreign key to agent (optional - for agent-based sessions)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)

    # Session metadata
    name = Column(String, nullable=True)  # Optional session name
    description = Column(String, nullable=True)  # Optional session description

    # Session status
    status = Column(String, default="active")  # active, inactive, completed, etc.
    is_active = Column(Boolean, default=True)

    # Container information (if applicable)
    container_id = Column(String, nullable=True)
    container_status = Column(String, nullable=True)
    base_url = Column(String, nullable=True)  # Custom base URL for agent containers
    opencode_session_id = Column(String, nullable=True)  # OpenCode internal session ID for persistence

    # Session data (JSON stored as string)
    auth_data = Column(String, nullable=True)  # JSON string for auth configuration
    environment_vars = Column(String, nullable=True)  # JSON string for environment variables

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, nullable=True)

    # Relationship back to user
    user = relationship("User", back_populates="sessions")

    # Relationship to agent
    agent = relationship("Agent")

    def __repr__(self):
        return f"<Session(session_id={self.session_id}, user_id={self.user_id}, status={self.status})>"

# Explicitly add Session to the module
import sys
current_module = sys.modules[__name__]
current_module.Session = Session


