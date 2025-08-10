"""
Web server configuration for YouTube to Notion integration.

This module provides configuration management for the web UI mode,
including FastAPI server settings and environment variable handling.
"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

from ..utils.exceptions import ConfigurationError


@dataclass
class WebServerConfig:
    """Configuration for the web server."""
    
    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8080
    debug: bool = False
    reload: bool = False
    
    # Static Files Configuration
    static_folder: str = "web/static"
    
    # Queue Configuration
    max_queue_size: int = 100
    
    # SSE Configuration
    sse_heartbeat_interval: int = 30
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.port <= 0 or self.port > 65535:
            raise ValueError("Port must be between 1 and 65535")
        
        if self.max_queue_size <= 0:
            raise ValueError("max_queue_size must be positive")
        
        if self.sse_heartbeat_interval <= 0:
            raise ValueError("sse_heartbeat_interval must be positive")
    
    @classmethod
    def from_environment(cls) -> 'WebServerConfig':
        """
        Create web server configuration from environment variables.
        
        Returns:
            WebServerConfig: Configured web server settings
        """
        # Load environment variables if not in test mode
        if os.getenv('TEST_MODE') != 'true':
            load_dotenv()
        
        return cls(
            host=os.getenv("WEB_HOST", "127.0.0.1"),
            port=int(os.getenv("WEB_PORT", "8080")),
            debug=os.getenv("WEB_DEBUG", "false").lower() == "true",
            reload=os.getenv("WEB_RELOAD", "false").lower() == "true",
            static_folder=os.getenv("WEB_STATIC_FOLDER", "web/static"),
            max_queue_size=int(os.getenv("WEB_MAX_QUEUE_SIZE", "100")),
            sse_heartbeat_interval=int(os.getenv("WEB_SSE_HEARTBEAT_INTERVAL", "30"))
        )