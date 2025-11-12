"""
Session Management Configuration
Centralized configuration for cleanup worker and recovery manager
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class SessionManagementConfig:
    """Configuration for session management services"""
    
    # Cleanup timeout in minutes
    idle_timeout_minutes: int = int(os.getenv("SESSION_IDLE_TIMEOUT_MINUTES", "15"))
    
    # How often to check for idle sessions (seconds)
    check_interval_seconds: int = int(os.getenv("SESSION_CHECK_INTERVAL_SECONDS", "60"))
    
    # Enable/disable the cleanup worker
    enable_cleanup_worker: bool = os.getenv("SESSION_ENABLE_CLEANUP_WORKER", "true").lower() == "true"
    
    # Enable/disable automatic session recovery
    enable_auto_recovery: bool = os.getenv("SESSION_ENABLE_AUTO_RECOVERY", "true").lower() == "true"
    
    # Container stop timeout in seconds
    container_stop_timeout: int = int(os.getenv("SESSION_CONTAINER_STOP_TIMEOUT", "10"))
    
    # Number of retries for container operations
    container_operation_retries: int = int(os.getenv("SESSION_CONTAINER_OPERATION_RETRIES", "3"))
    
    # Log level for session management
    log_level: str = os.getenv("SESSION_LOG_LEVEL", "INFO")
    
    @classmethod
    def from_env(cls) -> "SessionManagementConfig":
        """Load configuration from environment variables"""
        return cls()
    
    def validate(self) -> bool:
        """Validate configuration"""
        errors = []
        
        if self.idle_timeout_minutes < 1:
            errors.append("SESSION_IDLE_TIMEOUT_MINUTES must be >= 1")
        
        if self.check_interval_seconds < 5:
            errors.append("SESSION_CHECK_INTERVAL_SECONDS must be >= 5")
        
        if self.check_interval_seconds >= self.idle_timeout_minutes * 60:
            errors.append(
                "SESSION_CHECK_INTERVAL_SECONDS must be less than "
                f"SESSION_IDLE_TIMEOUT_MINUTES * 60 ({self.idle_timeout_minutes * 60})"
            )
        
        if self.container_stop_timeout < 1:
            errors.append("SESSION_CONTAINER_STOP_TIMEOUT must be >= 1")
        
        if self.container_operation_retries < 1:
            errors.append("SESSION_CONTAINER_OPERATION_RETRIES must be >= 1")
        
        if errors:
            error_msg = "\n".join(f"  - {e}" for e in errors)
            raise ValueError(f"Invalid session management configuration:\n{error_msg}")
        
        return True
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "idle_timeout_minutes": self.idle_timeout_minutes,
            "check_interval_seconds": self.check_interval_seconds,
            "enable_cleanup_worker": self.enable_cleanup_worker,
            "enable_auto_recovery": self.enable_auto_recovery,
            "container_stop_timeout": self.container_stop_timeout,
            "container_operation_retries": self.container_operation_retries,
            "log_level": self.log_level,
        }
    
    def __str__(self) -> str:
        """String representation"""
        items = [f"{k}={v}" for k, v in self.to_dict().items()]
        return f"SessionManagementConfig({', '.join(items)})"


# Global configuration instance
config: Optional[SessionManagementConfig] = None


def get_config() -> SessionManagementConfig:
    """Get or initialize global configuration"""
    global config
    
    if config is None:
        config = SessionManagementConfig.from_env()
        config.validate()
    
    return config


def init_config() -> SessionManagementConfig:
    """Initialize configuration (call at app startup)"""
    cfg = get_config()
    import logging
    logging.info(f"Session Management Config: {cfg}")
    return cfg
