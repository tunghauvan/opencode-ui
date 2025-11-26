"""
Schemas for OAuth and authentication
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
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


class SessionCreateRequest(BaseModel):
    """Session creation request schema"""
    session_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None


class SessionResponse(BaseModel):
    """Session response schema"""
    id: int
    session_id: str
    user_id: str
    agent_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    status: str
    is_active: bool
    container_id: Optional[str] = None
    container_status: Optional[str] = None
    base_url: Optional[str] = None
    auth_data: Optional[str] = None
    environment_vars: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_activity: Optional[datetime] = None

    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """Session list response schema"""
    sessions: list[SessionResponse]


# Message schemas matching OpenCode format
class MessagePartText(BaseModel):
    """Text part of a message"""
    type: str = "text"
    text: str


class MessagePartToolUse(BaseModel):
    """Tool use part of a message"""
    type: str = "tool_use"
    id: str
    name: str
    input: Dict[str, Any]


class MessagePartToolResult(BaseModel):
    """Tool result part of a message"""
    type: str = "tool_result"
    id: str
    content: Any


class MessageTimeInfo(BaseModel):
    """Time information for a message"""
    created: Optional[int] = None  # Unix timestamp in milliseconds


class MessageModelInfo(BaseModel):
    """Model information for a message"""
    providerID: Optional[str] = None
    modelID: Optional[str] = None


class MessageTokensInfo(BaseModel):
    """Token usage information"""
    input: Optional[int] = None
    output: Optional[int] = None


class MessageInfo(BaseModel):
    """Message info matching OpenCode format"""
    id: str
    sessionID: str
    role: str  # "user" or "assistant"
    time: Optional[MessageTimeInfo] = None
    model: Optional[MessageModelInfo] = None
    tokens: Optional[MessageTokensInfo] = None
    cost: Optional[float] = None

    class Config:
        extra = "ignore"  # Ignore extra fields


class MessageResponse(BaseModel):
    """Message response matching OpenCode format"""
    info: MessageInfo
    parts: List[Dict[str, Any]]

    class Config:
        from_attributes = True
        extra = "ignore"  # Ignore extra fields


class MessageListResponse(BaseModel):
    """List of messages response"""
    messages: List[MessageResponse]


class SyncMessagesRequest(BaseModel):
    """Request to sync messages from OpenCode agent"""
    force: bool = False  # Force full resync


class SyncMessagesResponse(BaseModel):
    """Response after syncing messages"""
    synced_count: int
    new_count: int
    updated_count: int
