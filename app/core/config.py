"""
Configuration settings for OpenCode CLI Tool
"""
import os
from typing import Optional

class Settings:
    """Application settings"""

    # OpenCode settings
    OPENCODE_BASE_URL: str = os.getenv("OPENCODE_BASE_URL", "http://localhost:4096")

    # Optional authentication
    OPENCODE_API_KEY: Optional[str] = os.getenv("OPENCODE_API_KEY")

settings = Settings()