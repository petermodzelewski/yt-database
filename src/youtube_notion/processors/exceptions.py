"""
Custom exception classes for YouTube processing errors.

This module defines the exception hierarchy for handling various error
scenarios that can occur during YouTube video processing, including
URL validation, API failures, and video availability issues.
"""


class YouTubeProcessingError(Exception):
    """
    Base exception for YouTube processing errors.
    
    This is the parent class for all YouTube processing related exceptions.
    It provides a common interface for handling errors in the processing pipeline.
    """
    
    def __init__(self, message: str, details: str = None):
        """
        Initialize the exception with a message and optional details.
        
        Args:
            message: Human-readable error message
            details: Optional additional details about the error
        """
        super().__init__(message)
        self.message = message
        self.details = details
    
    def __str__(self):
        if self.details:
            return f"{self.message}: {self.details}"
        return self.message


class InvalidURLError(YouTubeProcessingError):
    """
    Raised when YouTube URL is invalid or unsupported.
    
    This exception is raised when:
    - The provided URL is not a valid YouTube URL
    - The URL format is not supported by the processor
    - The URL cannot be parsed to extract a video ID
    """
    pass


class APIError(YouTubeProcessingError):
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


class VideoUnavailableError(YouTubeProcessingError):
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