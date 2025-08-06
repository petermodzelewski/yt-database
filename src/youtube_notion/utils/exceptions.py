"""
Exception hierarchy for the YouTube-to-Notion integration system.

This module defines a comprehensive exception hierarchy that provides
clear error categorization and enables proper error handling throughout
the application.
"""

from typing import Optional, List, Dict


class VideoProcessingError(Exception):
    """
    Base exception for all video processing errors.
    
    This is the root exception class for all errors that occur during
    video processing operations. It provides a common base for catching
    any processing-related error.
    """
    
    def __init__(self, message: str, details: str = None):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            details: Optional additional details for debugging
        """
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self):
        if self.details:
            return f"{self.message}\nDetails: {self.details}"
        return self.message


class ConfigurationError(VideoProcessingError):
    """
    Configuration validation errors.
    
    Raised when required configuration is missing, invalid, or incomplete.
    This includes missing API keys, invalid database names, or malformed
    configuration values.
    """
    
    def __init__(self, message: str, missing_vars: Optional[List[str]] = None, 
                 invalid_vars: Optional[Dict[str, str]] = None, details: str = None):
        """
        Initialize configuration error with validation details.
        
        Args:
            message: Human-readable error message
            missing_vars: List of missing required variables
            invalid_vars: Dictionary of invalid variables and their issues
            details: Additional error details
        """
        super().__init__(message, details)
        self.missing_vars = missing_vars or []
        self.invalid_vars = invalid_vars or {}


class MetadataExtractionError(VideoProcessingError):
    """
    Metadata extraction errors.
    
    Raised when video metadata cannot be extracted from YouTube.
    This includes invalid URLs, private videos, API failures, or
    web scraping failures.
    """
    pass


class SummaryGenerationError(VideoProcessingError):
    """
    Summary generation errors.
    
    Raised when AI summary generation fails. This includes API failures,
    quota exceeded errors, invalid responses, or processing timeouts.
    """
    pass


class StorageError(VideoProcessingError):
    """
    Storage operation errors.
    
    Raised when storing processed content fails. This includes database
    connection errors, permission issues, or storage backend failures.
    """
    pass


# YouTube-specific exceptions (moved from processors.exceptions to avoid circular imports)

class InvalidURLError(VideoProcessingError):
    """
    Raised when YouTube URL is invalid or unsupported.
    
    This exception is raised when:
    - The provided URL is not a valid YouTube URL
    - The URL format is not supported by the processor
    - The URL cannot be parsed to extract a video ID
    """
    pass


class APIError(VideoProcessingError):
    """
    Raised when API calls fail.
    
    This is a general exception for API-related failures that can occur
    when communicating with external services like YouTube Data API or
    Google Gemini API.
    """
    
    def __init__(self, message: str, api_name: str = None, status_code: int = None, details: str = None):
        """
        Initialize API error with additional context.
        
        Args:
            message: Human-readable error message
            api_name: Name of the API that failed (e.g., 'YouTube Data API', 'Gemini API')
            status_code: HTTP status code if applicable
            details: Additional error details
        """
        super().__init__(message, details)
        self.api_name = api_name
        self.status_code = status_code
    
    def __str__(self):
        parts = [self.message]
        if self.api_name:
            parts.append(f"API: {self.api_name}")
        if self.status_code:
            parts.append(f"Status: {self.status_code}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class VideoUnavailableError(VideoProcessingError):
    """
    Raised when video is private, deleted, or restricted.
    
    This exception is raised when:
    - The video is set to private by the owner
    - The video has been deleted from YouTube
    - The video is restricted in certain regions
    - The video requires age verification or other restrictions
    """
    
    def __init__(self, message: str, video_id: str = None, details: str = None):
        """
        Initialize with video-specific context.
        
        Args:
            message: Human-readable error message
            video_id: YouTube video ID that is unavailable
            details: Additional details about why the video is unavailable
        """
        super().__init__(message, details)
        self.video_id = video_id
    
    def __str__(self):
        parts = [self.message]
        if self.video_id:
            parts.append(f"Video ID: {self.video_id}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


class QuotaExceededError(APIError):
    """
    Raised when API quota limits are exceeded.
    
    This exception is raised when:
    - YouTube Data API quota is exceeded
    - Gemini API rate limits are hit
    - Daily or monthly usage limits are reached
    """
    
    def __init__(self, message: str, api_name: str = None, quota_type: str = None, 
                 reset_time: str = None, retry_delay_seconds: int = None, 
                 raw_error: dict = None):
        """
        Initialize with quota-specific information.
        
        Args:
            message: Human-readable error message
            api_name: Name of the API that hit quota limits
            quota_type: Type of quota exceeded (e.g., 'daily', 'per_minute')
            reset_time: When the quota will reset (if known)
            retry_delay_seconds: Seconds to wait before retrying (from API response)
            raw_error: Raw error response from API for detailed analysis
        """
        super().__init__(message, api_name=api_name)
        self.quota_type = quota_type
        self.reset_time = reset_time
        self.retry_delay_seconds = retry_delay_seconds
        self.raw_error = raw_error
    
    def __str__(self):
        parts = [self.message]
        if self.api_name:
            parts.append(f"API: {self.api_name}")
        if self.quota_type:
            parts.append(f"Quota Type: {self.quota_type}")
        if self.retry_delay_seconds:
            parts.append(f"Retry After: {self.retry_delay_seconds}s")
        if self.reset_time:
            parts.append(f"Resets: {self.reset_time}")
        if self.details:
            parts.append(f"Details: {self.details}")
        return " | ".join(parts)


# Legacy exception for backward compatibility
class YouTubeProcessingError(VideoProcessingError):
    """
    Legacy exception for backward compatibility.
    
    This is an alias for VideoProcessingError to maintain compatibility
    with existing code that uses YouTubeProcessingError.
    """
    pass