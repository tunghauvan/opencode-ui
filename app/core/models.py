"""
User and GitHub token models
"""
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Text, BigInteger
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

    # Relationship to messages
    messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")


class Message(Base):
    """
    Message model for storing session message history.
    Matches the OpenCode agent server message format.
    
    OpenCode message format:
    {
        "info": {
            "id": "msg_xxx",
            "sessionID": "session_xxx",
            "role": "user" | "assistant",
            "time": {"created": 1731000000000}
        },
        "parts": [
            {"type": "text", "text": "..."},
            {"type": "tool_use", "id": "...", "name": "...", "input": {...}},
            {"type": "tool_result", "id": "...", "content": "..."}
        ]
    }
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # OpenCode message ID (from info.id)
    message_id = Column(String, unique=True, index=True, nullable=False)
    
    # Foreign key to session (using session_id string, not the integer id)
    session_id = Column(String, ForeignKey("sessions.session_id"), nullable=False, index=True)
    
    # Message role: "user" or "assistant"
    role = Column(String, nullable=False, index=True)
    
    # Message parts stored as JSON string
    # Contains array of parts: [{type: "text", text: "..."}, {type: "tool_use", ...}]
    parts = Column(Text, nullable=False)
    
    # Timestamp from OpenCode (Unix timestamp in milliseconds)
    created_timestamp = Column(BigInteger, nullable=True)
    
    # Model information (for assistant messages)
    provider_id = Column(String, nullable=True)
    model_id = Column(String, nullable=True)
    
    # Token usage information
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    
    # Cost information
    cost = Column(String, nullable=True)  # Stored as string to preserve precision
    
    # Local timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship back to session
    session = relationship("Session", back_populates="messages")

    def __repr__(self):
        return f"<Message(message_id={self.message_id}, session_id={self.session_id}, role={self.role})>"

    def to_opencode_format(self) -> dict:
        """Convert to OpenCode message format"""
        import json
        return {
            "info": {
                "id": self.message_id,
                "sessionID": self.session_id,
                "role": self.role,
                "time": {"created": self.created_timestamp} if self.created_timestamp else None,
                "model": {
                    "providerID": self.provider_id,
                    "modelID": self.model_id
                } if self.provider_id and self.model_id else None,
                "tokens": {
                    "input": self.input_tokens,
                    "output": self.output_tokens
                } if self.input_tokens is not None or self.output_tokens is not None else None,
                "cost": float(self.cost) if self.cost else None
            },
            "parts": json.loads(self.parts) if isinstance(self.parts, str) else self.parts
        }

    @classmethod
    def from_opencode_format(cls, data: dict, session_id: str) -> "Message":
        """Create Message from OpenCode message format"""
        import json
        info = data.get("info", {})
        time_info = info.get("time", {})
        model_info = info.get("model", {})
        tokens_info = info.get("tokens", {})
        
        return cls(
            message_id=info.get("id"),
            session_id=session_id,
            role=info.get("role", "user"),
            parts=json.dumps(data.get("parts", [])),
            created_timestamp=time_info.get("created") if time_info else None,
            provider_id=model_info.get("providerID") if model_info else None,
            model_id=model_info.get("modelID") if model_info else None,
            input_tokens=tokens_info.get("input") if tokens_info else None,
            output_tokens=tokens_info.get("output") if tokens_info else None,
            cost=str(info.get("cost")) if info.get("cost") is not None else None
        )


# Explicitly add Session and Message to the module
import sys
current_module = sys.modules[__name__]
current_module.Session = Session
current_module.Message = Message


