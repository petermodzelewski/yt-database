"""
Abstract interface for storing processed video content.

This module defines the Storage interface that enables pluggable implementations
for different storage backends (Notion, databases, file systems, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class Storage(ABC):
    """Abstract interface for storing processed video content."""
    
    @abstractmethod
    def store_video_summary(self, video_data: Dict[str, Any]) -> bool:
        """
        Store processed video data.
        
        Args:
            video_data: Processed video data containing:
                - Title: Video title
                - Channel: Channel name
                - Video URL: Original YouTube URL
                - Cover: Thumbnail URL
                - Summary: Generated markdown summary
                - Additional metadata as needed
                
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            StorageError: If storage operation fails
            ConfigurationError: If storage backend is not properly configured
        """
        pass
    
    @abstractmethod
    def validate_configuration(self) -> bool:
        """
        Validate that the storage backend is properly configured.
        
        Returns:
            bool: True if configuration is valid, False otherwise
            
        Raises:
            ConfigurationError: If configuration validation fails
        """
        pass
    
    @abstractmethod
    def find_target_location(self) -> Optional[str]:
        """
        Find and return the target storage location identifier.
        
        Returns:
            Optional[str]: Storage location identifier (e.g., database ID, 
                          directory path) if found, None otherwise
                          
        Raises:
            StorageError: If location discovery fails
            ConfigurationError: If storage backend is not properly configured
        """
        pass