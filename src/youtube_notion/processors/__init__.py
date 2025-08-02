"""
YouTube video processing module.

This module contains processors for handling YouTube video data extraction,
metadata retrieval, and AI-powered summary generation.
"""

from .youtube_processor import YouTubeProcessor
from .exceptions import (
    YouTubeProcessingError,
    InvalidURLError,
    APIError,
    VideoUnavailableError,
    QuotaExceededError
)

__all__ = [
    'YouTubeProcessor',
    'YouTubeProcessingError',
    'InvalidURLError',
    'APIError',
    'VideoUnavailableError',
    'QuotaExceededError'
]