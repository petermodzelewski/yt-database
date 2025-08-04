"""
Video metadata extractor for YouTube videos.

This module contains the VideoMetadataExtractor class that handles URL validation,
video ID extraction, and metadata retrieval from YouTube using both API and
web scraping approaches.
"""

import os
import re
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from ..utils.exceptions import (
    InvalidURLError,
    APIError,
    VideoUnavailableError,
    QuotaExceededError,
    MetadataExtractionError,
    ConfigurationError
)


class VideoMetadataExtractor:
    """
    Extracts metadata from YouTube videos using API or web scraping.
    
    This class handles the complete metadata extraction pipeline:
    1. URL validation and video ID extraction
    2. Video metadata retrieval from YouTube Data API (if available)
    3. Fallback to web scraping when API is not available
    4. Error handling and retry logic
    """
    
    def __init__(self, youtube_api_key: Optional[str] = None, timeout_seconds: int = 10):
        """
        Initialize the metadata extractor.
        
        Args:
            youtube_api_key: YouTube Data API key for metadata extraction (optional)
            timeout_seconds: Timeout for web scraping requests (default: 10)
            
        Raises:
            ConfigurationError: If configuration parameters are invalid
        """
        # Validate configuration parameters
        if timeout_seconds <= 0:
            raise ConfigurationError(
                "Timeout seconds must be positive",
                details=f"Received: {timeout_seconds}"
            )
        
        self.youtube_api_key = youtube_api_key
        self.timeout_seconds = timeout_seconds
    
    def validate_configuration(self) -> bool:
        """
        Validate that the metadata extractor is properly configured.
        
        Returns:
            bool: True if configuration is valid, False otherwise
            
        Raises:
            ConfigurationError: If configuration validation fails
        """
        try:
            # Validate timeout
            if self.timeout_seconds <= 0:
                raise ConfigurationError("Timeout seconds must be positive")
            
            # If YouTube API key is provided, validate it's not empty
            if self.youtube_api_key is not None and not self.youtube_api_key.strip():
                raise ConfigurationError("YouTube API key cannot be empty if provided")
            
            # Test YouTube API key if provided (without making actual API call)
            if self.youtube_api_key:
                try:
                    # Just test that we can create the YouTube service
                    build('youtube', 'v3', developerKey=self.youtube_api_key, cache_discovery=False)
                except Exception as e:
                    raise ConfigurationError(
                        f"Invalid YouTube API key or service initialization failed: {str(e)}",
                        details="Verify your YouTube Data API key is valid and has necessary permissions"
                    )
            
            return True
            
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(
                f"Configuration validation failed: {str(e)}"
            )
    
    def validate_url(self, url: str) -> bool:
        """
        Validate if a URL is a supported YouTube URL.
        
        This method checks if the provided URL is a valid YouTube URL
        that can be processed by this system. It performs the same
        validation as extract_video_id but returns a boolean instead
        of raising exceptions.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is valid and supported, False otherwise
        """
        try:
            self.extract_video_id(url)
            return True
        except InvalidURLError:
            return False
    
    def extract_video_id(self, url: str) -> str:
        """
        Extract video ID from YouTube URL.
        
        Supports multiple YouTube URL formats:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/watch?v=VIDEO_ID&t=123s (with timestamp)
        - https://m.youtube.com/watch?v=VIDEO_ID
        - https://youtube.com/watch?v=VIDEO_ID (without www)
        
        Args:
            url: YouTube URL to parse
            
        Returns:
            str: Extracted video ID (11 characters)
            
        Raises:
            InvalidURLError: If URL format is not supported or video ID cannot be extracted
        """
        if not url or not isinstance(url, str):
            raise InvalidURLError("URL must be a non-empty string", details=f"Received: {type(url).__name__}")
        
        # Clean up the URL - remove whitespace
        url = url.strip()
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        try:
            parsed_url = urlparse(url)
        except Exception as e:
            raise InvalidURLError("Invalid URL format", details=str(e))
        
        # Check if it's a YouTube domain
        valid_domains = ['youtube.com', 'www.youtube.com', 'm.youtube.com', 'youtu.be']
        if parsed_url.netloc.lower() not in valid_domains:
            raise InvalidURLError(
                "URL is not from a supported YouTube domain",
                details=f"Domain: {parsed_url.netloc}, Supported: {', '.join(valid_domains)}"
            )
        
        video_id = None
        
        # Handle youtu.be short URLs
        if parsed_url.netloc.lower() == 'youtu.be':
            # For youtu.be/VIDEO_ID, the video ID is in the path
            path_parts = parsed_url.path.strip('/').split('/')
            if path_parts and path_parts[0]:
                video_id = path_parts[0]
        
        # Handle youtube.com URLs
        elif parsed_url.netloc.lower() in ['youtube.com', 'www.youtube.com', 'm.youtube.com']:
            # Check for /watch URLs
            if parsed_url.path == '/watch':
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params and query_params['v']:
                    video_id = query_params['v'][0]
            
            # Check for /embed/ URLs
            elif parsed_url.path.startswith('/embed/'):
                path_parts = parsed_url.path.split('/')
                if len(path_parts) >= 3 and path_parts[2]:
                    video_id = path_parts[2]
            
            # Check for /v/ URLs (legacy format)
            elif parsed_url.path.startswith('/v/'):
                path_parts = parsed_url.path.split('/')
                if len(path_parts) >= 3 and path_parts[2]:
                    video_id = path_parts[2]
        
        # Validate the extracted video ID
        if not video_id:
            raise InvalidURLError(
                "Could not extract video ID from URL",
                details=f"URL path: {parsed_url.path}, Query: {parsed_url.query}"
            )
        
        # Clean video ID (remove any additional parameters)
        video_id = video_id.split('&')[0].split('?')[0]
        
        # Validate video ID format (YouTube video IDs are 11 characters, alphanumeric + - and _)
        if not self._is_valid_video_id(video_id):
            raise InvalidURLError(
                "Extracted video ID has invalid format",
                details=f"Video ID: {video_id}, Expected: 11 alphanumeric characters"
            )
        
        return video_id
    
    def extract_metadata(self, video_url: str) -> Dict[str, Any]:
        """
        Extract video metadata from YouTube URL.
        
        This is the main entry point for metadata extraction. It first extracts
        the video ID from the URL, then retrieves metadata using either the
        YouTube Data API (if available) or web scraping as a fallback.
        
        Args:
            video_url: Valid YouTube URL to process
            
        Returns:
            dict: Video metadata containing:
                - title: Video title
                - channel: Channel name
                - description: Video description (if available)
                - published_at: Publication date (if available)
                - thumbnail_url: Thumbnail URL
                - video_id: Extracted video ID
                
        Raises:
            InvalidURLError: If YouTube URL is invalid
            APIError: If API calls fail
            VideoUnavailableError: If video is unavailable
            MetadataExtractionError: If metadata extraction fails
        """
        try:
            # Step 1: Validate URL and extract video ID
            video_id = self.extract_video_id(video_url)
            
            # Step 2: Get video metadata from YouTube
            metadata = self._get_video_metadata(video_id)
            
            # Step 3: Add video ID to metadata
            metadata['video_id'] = video_id
            
            return metadata
            
        except (InvalidURLError, APIError, VideoUnavailableError, QuotaExceededError):
            # Re-raise known exceptions as-is
            raise
            
        except Exception as e:
            # Wrap unexpected errors in a metadata extraction error
            raise MetadataExtractionError(
                f"Unexpected error during metadata extraction: {str(e)}",
                details=f"URL: {video_url}, Error type: {type(e).__name__}"
            )
    
    def _is_valid_video_id(self, video_id: str) -> bool:
        """
        Validate YouTube video ID format.
        
        YouTube video IDs are 11 characters long and contain:
        - Letters (a-z, A-Z)
        - Numbers (0-9)
        - Hyphens (-)
        - Underscores (_)
        
        Args:
            video_id: Video ID to validate
            
        Returns:
            bool: True if video ID format is valid
        """
        if not video_id or not isinstance(video_id, str):
            return False
        
        # YouTube video IDs are exactly 11 characters
        if len(video_id) != 11:
            return False
        
        # Check if all characters are valid (alphanumeric, hyphen, underscore)
        return re.match(r'^[a-zA-Z0-9_-]{11}$', video_id) is not None
    
    def _get_video_metadata(self, video_id: str) -> Dict[str, str]:
        """
        Get video title, channel, and thumbnail from YouTube.
        
        Uses YouTube Data API v3 if available, otherwise falls back to web scraping.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            dict: Video metadata containing title, channel, and other info
            
        Raises:
            APIError: If API calls fail
            VideoUnavailableError: If video is not accessible
        """
        if self.youtube_api_key:
            return self._get_metadata_via_api(video_id)
        else:
            return self._get_metadata_via_scraping(video_id)
    
    def _get_metadata_via_api(self, video_id: str) -> Dict[str, str]:
        """
        Get video metadata using YouTube Data API v3.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            dict: Video metadata containing title, channel, and other info
            
        Raises:
            APIError: If API calls fail
            VideoUnavailableError: If video is not accessible
            QuotaExceededError: If API quota is exceeded
        """
        try:
            # Build YouTube API client
            youtube = build('youtube', 'v3', developerKey=self.youtube_api_key)
            
            # Request video details
            request = youtube.videos().list(
                part='snippet',
                id=video_id
            )
            
            response = request.execute()
            
            # Check if video exists
            if not response.get('items'):
                raise VideoUnavailableError(
                    "Video not found or is not accessible",
                    video_id=video_id,
                    details="Video may be private, deleted, or restricted"
                )
            
            # Extract video information
            video_info = response['items'][0]['snippet']
            
            return {
                'title': video_info.get('title', 'Unknown Title'),
                'channel': video_info.get('channelTitle', 'Unknown Channel'),
                'description': video_info.get('description', ''),
                'published_at': video_info.get('publishedAt', ''),
                'thumbnail_url': self._construct_thumbnail_url(video_id)
            }
            
        except VideoUnavailableError:
            # Re-raise VideoUnavailableError as-is
            raise
        
        except HttpError as e:
            error_details = e.error_details[0] if e.error_details else {}
            error_reason = error_details.get('reason', 'unknown')
            error_message = error_details.get('message', str(e))
            
            # Handle quota exceeded errors
            if e.resp.status == 403 and error_reason in ['quotaExceeded', 'dailyLimitExceeded']:
                quota_type = 'daily' if error_reason == 'dailyLimitExceeded' else 'per_minute'
                raise QuotaExceededError(
                    f"YouTube API quota exceeded: {error_message}",
                    api_name="YouTube Data API",
                    quota_type=quota_type
                )
            
            # Handle rate limiting (429 status)
            elif e.resp.status == 429:
                raise QuotaExceededError(
                    f"YouTube API rate limit exceeded: {error_message}",
                    api_name="YouTube Data API",
                    quota_type="rate_limit"
                )
            
            # Handle authentication errors
            elif e.resp.status == 401:
                raise APIError(
                    f"YouTube API authentication failed: {error_message}. Check your API key.",
                    api_name="YouTube Data API",
                    status_code=e.resp.status,
                    details="Verify your YouTube Data API key is valid and has the necessary permissions"
                )
            
            # Handle forbidden access
            elif e.resp.status == 403 and error_reason != 'quotaExceeded':
                raise APIError(
                    f"YouTube API access forbidden: {error_message}. Check API key permissions.",
                    api_name="YouTube Data API",
                    status_code=e.resp.status,
                    details="Your API key may not have permission to access the YouTube Data API"
                )
            
            # Handle not found errors
            elif e.resp.status == 404:
                raise VideoUnavailableError(
                    f"Video not found: {error_message}",
                    video_id=video_id,
                    details="The video may have been deleted or made private"
                )
            
            # Handle other API errors
            raise APIError(
                f"YouTube API request failed: {error_message}",
                api_name="YouTube Data API",
                status_code=e.resp.status,
                details=f"Error reason: {error_reason}, Video ID: {video_id}"
            )
        
        except Exception as e:
            raise APIError(
                f"Unexpected error during YouTube API call: {str(e)}",
                api_name="YouTube Data API",
                details=str(e)
            )
    
    def _get_metadata_via_scraping(self, video_id: str) -> Dict[str, str]:
        """
        Get video metadata using web scraping as fallback.
        
        This method scrapes the YouTube page to extract basic metadata
        when the YouTube Data API is not available.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            dict: Video metadata containing title, channel, and other info
            
        Raises:
            APIError: If scraping fails
            VideoUnavailableError: If video is not accessible
        """
        try:
            # Construct YouTube URL
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Set headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Make request with timeout
            response = requests.get(url, headers=headers, timeout=self.timeout_seconds)
            response.raise_for_status()
            
            html_content = response.text
            
            # Extract title using regex
            title_match = re.search(r'"title":"([^"]+)"', html_content)
            title = title_match.group(1) if title_match else "Unknown Title"
            
            # Extract channel name using regex
            channel_match = re.search(r'"ownerChannelName":"([^"]+)"', html_content)
            if not channel_match:
                # Try alternative pattern
                channel_match = re.search(r'"channelName":"([^"]+)"', html_content)
            channel = channel_match.group(1) if channel_match else "Unknown Channel"
            
            # Check if video is available
            if "Video unavailable" in html_content or "This video is not available" in html_content:
                raise VideoUnavailableError(
                    "Video is not available",
                    video_id=video_id,
                    details="Video may be private, deleted, or restricted"
                )
            
            # Properly decode JSON-escaped unicode sequences
            import json
            try:
                # Use JSON decoder to properly handle unicode escapes while preserving UTF-8
                title = json.loads(f'"{title}"')
                channel = json.loads(f'"{channel}"')
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If JSON decoding fails, use the raw strings
                # This handles cases where the strings don't contain escape sequences
                pass
            
            return {
                'title': title,
                'channel': channel,
                'description': '',  # Not easily extractable via scraping
                'published_at': '',  # Not easily extractable via scraping
                'thumbnail_url': self._construct_thumbnail_url(video_id)
            }
            
        except VideoUnavailableError:
            # Re-raise VideoUnavailableError as-is
            raise
        
        except requests.RequestException as e:
            # Provide more specific error messages based on the type of request exception
            if isinstance(e, requests.exceptions.Timeout):
                error_msg = f"Request timed out while scraping YouTube page: {str(e)}"
                details = f"URL: https://www.youtube.com/watch?v={video_id}, Timeout: {self.timeout_seconds}s. Try increasing timeout or check network connection."
            elif isinstance(e, requests.exceptions.ConnectionError):
                error_msg = f"Connection error while scraping YouTube page: {str(e)}"
                details = f"URL: https://www.youtube.com/watch?v={video_id}. Check your internet connection."
            elif isinstance(e, requests.exceptions.HTTPError):
                status_code = getattr(e.response, 'status_code', 'unknown')
                error_msg = f"HTTP error {status_code} while scraping YouTube page: {str(e)}"
                if status_code == 429:
                    details = f"URL: https://www.youtube.com/watch?v={video_id}. YouTube is rate limiting requests. Try again later."
                elif status_code in [403, 404]:
                    details = f"URL: https://www.youtube.com/watch?v={video_id}. Video may be private, deleted, or restricted."
                else:
                    details = f"URL: https://www.youtube.com/watch?v={video_id}. HTTP status: {status_code}"
            else:
                error_msg = f"Failed to scrape YouTube page: {str(e)}"
                details = f"URL: https://www.youtube.com/watch?v={video_id}, Error type: {type(e).__name__}"
            
            raise APIError(
                error_msg,
                api_name="Web Scraping",
                details=details
            )
        
        except Exception as e:
            raise APIError(
                f"Unexpected error during web scraping: {str(e)}",
                api_name="Web Scraping",
                details=f"Video ID: {video_id}"
            )
    
    def _construct_thumbnail_url(self, video_id: str) -> str:
        """
        Construct YouTube thumbnail URL using video ID.
        
        YouTube provides several thumbnail sizes:
        - maxresdefault.jpg (1280x720) - highest quality, not always available
        - hqdefault.jpg (480x360) - high quality, usually available
        - mqdefault.jpg (320x180) - medium quality
        - default.jpg (120x90) - default quality
        
        This method returns the maxresdefault URL as it provides the best
        quality for Notion page covers.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            str: Thumbnail URL (maxresdefault.jpg format)
        """
        return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"