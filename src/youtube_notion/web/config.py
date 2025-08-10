"""
Configuration management for the web server.

This module provides Pydantic-based configuration management for the
FastAPI web server, supporting environment variable configuration
and validation.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
import os


class WebServerConfig(BaseModel):
    """
    Configuration model for the web server.
    
    Supports environment variable configuration with the WEB_ prefix.
    For example, WEB_HOST, WEB_PORT, WEB_DEBUG, etc.
    """
    
    host: str = Field(default="127.0.0.1", description="Server host address")
    port: int = Field(default=8080, description="Server port number")
    debug: bool = Field(default=False, description="Enable debug mode")
    static_folder: str = Field(default="web/static", description="Static files directory")
    max_queue_size: int = Field(default=100, description="Maximum queue size")
    sse_heartbeat_interval: int = Field(default=30, description="SSE heartbeat interval in seconds")
    reload: bool = Field(default=False, description="Enable uvicorn auto-reload for development")
    cors_origins: list[str] = Field(
        default=["http://localhost:8080", "http://127.0.0.1:8080"],
        description="Allowed CORS origins"
    )
    
    model_config = ConfigDict(
        env_prefix="WEB_",  # Allow WEB_HOST, WEB_PORT, etc.
        case_sensitive=False
    )
    
    @classmethod
    def from_env(cls) -> 'WebServerConfig':
        """
        Create configuration from environment variables.
        
        Returns:
            WebServerConfig: Configuration instance with values from environment
        """
        return cls(
            host=os.getenv("WEB_HOST", "127.0.0.1"),
            port=int(os.getenv("WEB_PORT", "8080")),
            debug=os.getenv("WEB_DEBUG", "false").lower() == "true",
            static_folder=os.getenv("WEB_STATIC_FOLDER", "web/static"),
            max_queue_size=int(os.getenv("WEB_MAX_QUEUE_SIZE", "100")),
            sse_heartbeat_interval=int(os.getenv("WEB_SSE_HEARTBEAT_INTERVAL", "30")),
            reload=os.getenv("WEB_RELOAD", "false").lower() == "true",
            cors_origins=os.getenv("WEB_CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")
        )