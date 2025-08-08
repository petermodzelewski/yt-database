"""
Abstract interface for generating video summaries.

This module defines the SummaryWriter interface that enables pluggable
implementations for different AI providers or summary generation strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class SummaryWriter(ABC):
    """Abstract interface for generating video summaries."""
    
    @abstractmethod
    def generate_summary(self, video_url: str, video_metadata: Dict[str, Any], 
                        custom_prompt: Optional[str] = None,
                        status_callback: Optional[callable] = None) -> str:
        """
        Generate a markdown summary for the video.
        
        Args:
            video_url: YouTube URL to process
            video_metadata: Video metadata (title, channel, description, etc.)
            custom_prompt: Optional custom prompt for generation
            status_callback: Optional callback for status updates
            
        Returns:
            str: Markdown summary with timestamps and rich formatting
            
        Raises:
            SummaryGenerationError: If summary generation fails
            ConfigurationError: If the writer is not properly configured
        """
        pass
    
    @abstractmethod
    def validate_configuration(self) -> bool:
        """
        Validate that the summary writer is properly configured.
        
        Returns:
            bool: True if configuration is valid, False otherwise
            
        Raises:
            ConfigurationError: If configuration validation fails
        """
        pass