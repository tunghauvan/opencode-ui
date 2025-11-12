"""
Backend utilities and decorators
"""
from functools import wraps
from typing import Callable, Any, Optional
from datetime import datetime
import logging
import asyncio

# Setup logging
logger = logging.getLogger(__name__)


def track_session_activity(func: Callable) -> Callable:
    """Decorator to track session activity automatically"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            logger.info(f"Session activity tracked: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            logger.info(f"Session activity tracked: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            raise

    # Return appropriate wrapper based on async/sync
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper


class SessionValidator:
    """Validator for session operations"""

    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """Validate session_id format"""
        if not session_id or not isinstance(session_id, str):
            return False
        if len(session_id) < 3 or len(session_id) > 255:
            return False
        # Allow alphanumeric, hyphens, underscores
        return all(c.isalnum() or c in '-_' for c in session_id)

    @staticmethod
    def validate_session_name(name: Optional[str]) -> bool:
        """Validate session name"""
        if name is None:
            return True
        if not isinstance(name, str):
            return False
        return len(name) <= 255

    @staticmethod
    def validate_environment_vars(env_vars: Optional[dict]) -> bool:
        """Validate environment variables"""
        if env_vars is None:
            return True
        if not isinstance(env_vars, dict):
            return False
        for key, value in env_vars.items():
            if not isinstance(key, str) or not isinstance(value, str):
                return False
        return True


class ContainerValidator:
    """Validator for container operations"""

    @staticmethod
    def validate_image_name(image: str) -> bool:
        """Validate Docker image name"""
        if not image or not isinstance(image, str):
            return False
        # Basic validation for image names
        # Format: [registry/]repository[:tag]
        return len(image) > 0 and len(image) < 255

    @staticmethod
    def validate_container_id(container_id: str) -> bool:
        """Validate container ID"""
        if not container_id or not isinstance(container_id, str):
            return False
        # Docker container IDs are typically 12-64 character hex strings
        return len(container_id) >= 12 and all(c in '0123456789abcdef' for c in container_id.lower())


class ErrorHandler:
    """Centralized error handling"""

    class SessionError(Exception):
        """Base session error"""
        pass

    class SessionNotFoundError(SessionError):
        """Session not found"""
        pass

    class SessionAlreadyExistsError(SessionError):
        """Session already exists"""
        pass

    class ContainerError(Exception):
        """Base container error"""
        pass

    class ContainerStartError(ContainerError):
        """Container failed to start"""
        pass

    class ContainerStopError(ContainerError):
        """Container failed to stop"""
        pass

    @staticmethod
    def handle_error(error: Exception) -> dict:
        """Convert exceptions to error responses"""
        error_map = {
            ErrorHandler.SessionNotFoundError: (404, "Session not found"),
            ErrorHandler.SessionAlreadyExistsError: (409, "Session already exists"),
            ErrorHandler.ContainerStartError: (500, "Failed to start container"),
            ErrorHandler.ContainerStopError: (500, "Failed to stop container"),
            ValueError: (400, "Invalid request"),
            Exception: (500, "Internal server error")
        }

        error_type = type(error)
        status_code, message = error_map.get(error_type, (500, "Internal server error"))

        return {
            "status_code": status_code,
            "message": message,
            "error": str(error)
        }
