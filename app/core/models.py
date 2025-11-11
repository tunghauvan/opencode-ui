"""
User and GitHub token models
"""
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base
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

    def __repr__(self):
        return f"<User(github_login={self.github_login}, github_id={self.github_id})>"
