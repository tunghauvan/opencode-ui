"""
Schemas for OAuth and authentication
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GitHubUserResponse(BaseModel):
    """GitHub user response schema"""
    id: str
    github_login: str
    github_id: str
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response schema"""
    user: GitHubUserResponse
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: Optional[int] = None
    token_expires_at: Optional[str] = None


class AuthorizationUrlResponse(BaseModel):
    """Authorization URL response schema"""
    authorization_url: str
    state: str


class TokenRefreshResponse(BaseModel):
    """Token refresh response schema"""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    expires_in: Optional[int] = None
