"""
YouTube video processor for extracting metadata and generating AI summaries.

This module contains the main YouTubeProcessor class that orchestrates
the entire YouTube video processing pipeline, from URL validation to
AI-powered summary generation.
"""

import re
import time
import requests
from typing import Optional, Dict, Any
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.genai as genai
from google.genai import types
from ..config.settings import YouTubeProcessorConfig, DEFAULT_SUMMARY_PROMPT
from ..utils.chat_logger import ChatLogger
from .exceptions import (
    YouTubeProcessingError,
    InvalidURLError,
    APIError,
    VideoUnavailableError,
    QuotaExceededError
)


class YouTubeProcessor:
    """
    Processes YouTube videos to generate structured data for Notion integration.
    
    This class handles the complete pipeline of YouTube video processing:
    1. URL validation and video ID extraction
    2. Video metadata retrieval from YouTube
    3. AI-powered summary generation using Google Gemini
    4. Data structure formatting for Notion compatibility
    
    The processor is designed to be compatible with the existing EXAMPLE_DATA
    format used by the Notion integration system.
    """
    
    def __init__(self, config: YouTubeProcessorConfig):
        """
        Initialize the YouTube processor with configuration.
        
        Args:
            config: YouTubeProcessorConfig object with all settings
        
        Raises:
            ValueError: If configuration is invalid
        """
        if not isinstance(config, YouTubeProcessorConfig):
            raise ValueError("config must be a YouTubeProcessorConfig instance")
        
        self.config = config
        
        # For backward compatibility, expose config values as instance attributes
        self.gemini_api_key = config.gemini_api_key
        self.youtube_api_key = config.youtube_api_key
        self.default_prompt = config.default_prompt
        self.max_retries = config.max_retries
        self.timeout_seconds = config.timeout_seconds
        
        # Initialize chat logger
        self.chat_logger = ChatLogger()
    
    @classmethod
    def from_api_keys(cls, gemini_api_key: str, youtube_api_key: Optional[str] = None, 
                      default_prompt: str = DEFAULT_SUMMARY_PROMPT, max_retries: int = 3, 
                      timeout_seconds: int = 120) -> 'YouTubeProcessor':
        """
        Create YouTubeProcessor from individual API keys (backward compatibility).
        
        Args:
            gemini_api_key: Google Gemini API key for AI summary generation
            youtube_api_key: YouTube Data API key for metadata extraction (optional)
            default_prompt: Default prompt for Gemini API (optional)
            max_retries: Maximum number of retries for API calls (default: 3)
            timeout_seconds: Timeout for API calls in seconds (default: 120)
        
        Returns:
            YouTubeProcessor: Configured processor instance
        """
        config = YouTubeProcessorConfig(
            gemini_api_key=gemini_api_key,
            youtube_api_key=youtube_api_key,
            default_prompt=default_prompt,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds
        )
        return cls(config)
    
    def validate_youtube_url(self, url: str) -> bool:
        """
        Validate if a URL is a supported YouTube URL.
        
        This method checks if the provided URL is a valid YouTube URL
        that can be processed by this system. It performs the same
        validation as _extract_video_id but returns a boolean instead
        of raising exceptions.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is valid and supported, False otherwise
        """
        try:
            self._extract_video_id(url)
            return True
        except InvalidURLError:
            return False
    
    def process_video(self, youtube_url: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a YouTube video and return structured data.
        
        This is the main entry point for video processing. It orchestrates
        the entire pipeline and returns data compatible with the existing
        EXAMPLE_DATA format.
        
        Args:
            youtube_url: Valid YouTube URL to process
            custom_prompt: Optional custom prompt for Gemini (uses default if None)
            
        Returns:
            dict: Data structure compatible with EXAMPLE_DATA format containing:
                - Title: Video title from YouTube metadata
                - Channel: Channel name from YouTube metadata  
                - Video URL: Original YouTube URL
                - Cover: Thumbnail URL (maxresdefault.jpg)
                - Summary: AI-generated markdown summary with timestamps
                
        Raises:
            InvalidURLError: If YouTube URL is invalid
            APIError: If API calls fail
            VideoUnavailableError: If video is unavailable
            ProcessingError: If video processing fails
        """
        try:
            # Step 1: Validate URL and extract video ID
            video_id = self._extract_video_id(youtube_url)
            
            # Step 2: Get video metadata from YouTube
            metadata = self._get_video_metadata(video_id)
            
            # Step 3: Generate AI summary using Gemini
            summary = self._generate_summary(youtube_url, custom_prompt, metadata)
            
            # Step 4: Construct response data structure matching EXAMPLE_DATA format
            result = {
                "Title": metadata['title'],
                "Channel": metadata['channel'],
                "Video URL": youtube_url,
                "Cover": metadata['thumbnail_url'],
                "Summary": summary
            }
            
            return result
            
        except (InvalidURLError, APIError, VideoUnavailableError, QuotaExceededError):
            # Re-raise known exceptions as-is
            raise
            
        except Exception as e:
            # Wrap unexpected errors in a generic processing error
            raise YouTubeProcessingError(
                f"Unexpected error during video processing: {str(e)}",
                details=f"URL: {youtube_url}, Error type: {type(e).__name__}"
            )
    
    def _extract_video_id(self, url: str) -> str:
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
            response = requests.get(url, headers=headers, timeout=10)
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
                details = f"URL: {url}, Timeout: {self.timeout_seconds}s. Try increasing timeout or check network connection."
            elif isinstance(e, requests.exceptions.ConnectionError):
                error_msg = f"Connection error while scraping YouTube page: {str(e)}"
                details = f"URL: {url}. Check your internet connection."
            elif isinstance(e, requests.exceptions.HTTPError):
                status_code = getattr(e.response, 'status_code', 'unknown')
                error_msg = f"HTTP error {status_code} while scraping YouTube page: {str(e)}"
                if status_code == 429:
                    details = f"URL: {url}. YouTube is rate limiting requests. Try again later."
                elif status_code in [403, 404]:
                    details = f"URL: {url}. Video may be private, deleted, or restricted."
                else:
                    details = f"URL: {url}. HTTP status: {status_code}"
            else:
                error_msg = f"Failed to scrape YouTube page: {str(e)}"
                details = f"URL: {url}, Error type: {type(e).__name__}"
            
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
    
    def _generate_summary(self, video_url: str, prompt: Optional[str] = None, 
                         video_metadata: Optional[Dict[str, str]] = None) -> str:
        """
        Generate AI summary using Google Gemini.
        
        This method uses the Google Gemini API to generate a markdown summary
        of the YouTube video content. It includes streaming response handling,
        retry logic, and comprehensive error handling.
        
        Args:
            video_url: YouTube URL for Gemini to process
            prompt: Prompt for summary generation (uses default if None)
            video_metadata: Optional video metadata for logging
            
        Returns:
            str: AI-generated markdown summary with timestamps
            
        Raises:
            APIError: If Gemini API call fails
            QuotaExceededError: If API quota is exceeded
        """
        if prompt is None:
            prompt = self.default_prompt
        
        # Generate summary with retry logic
        response = self._api_call_with_retry(self._call_gemini_api, video_url, prompt)
        
        # Log the chat conversation
        try:
            video_id = self._extract_video_id(video_url)
            self.chat_logger.log_chat(
                video_id=video_id,
                video_url=video_url,
                prompt=prompt,
                response=response,
                video_metadata=video_metadata
            )
        except Exception as e:
            # Don't fail the main process if logging fails
            print(f"Warning: Failed to log chat conversation: {e}")
        
        return response
    
    def _call_gemini_api(self, video_url: str, prompt: str) -> str:
        """
        Make the actual Gemini API call with streaming response handling.
        
        Args:
            video_url: YouTube URL for Gemini to process
            prompt: Prompt for summary generation
            
        Returns:
            str: AI-generated markdown summary with timestamps
            
        Raises:
            APIError: If Gemini API call fails
            QuotaExceededError: If API quota is exceeded
        """
        try:
            # Initialize Gemini client
            client = genai.Client(api_key=self.gemini_api_key)
            model = self.config.gemini_model
            
            # Prepare content for the API call
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part(
                            file_data=types.FileData(
                                file_uri=video_url,
                                mime_type="video/*"
                            )
                        ),
                        types.Part.from_text(text=prompt)
                    ]
                )
            ]
            
            # Configure generation settings using config values
            generate_content_config = types.GenerateContentConfig(
                temperature=self.config.gemini_temperature,
                max_output_tokens=self.config.gemini_max_output_tokens,
                response_mime_type="text/plain"
            )
            
            # Stream response and collect full text
            full_response = ""
            
            try:
                for chunk in client.models.generate_content_stream(
                    model=model,
                    contents=contents,
                    config=generate_content_config
                ):
                    if chunk.text:
                        full_response += chunk.text
            
            except Exception as stream_error:
                # If streaming fails, try non-streaming approach
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=generate_content_config
                )
                full_response = response.text if response.text else ""
            
            # Validate response
            if not full_response or not full_response.strip():
                raise APIError(
                    "Gemini API returned empty response",
                    api_name="Gemini API",
                    details="The API call succeeded but returned no content"
                )
            
            return full_response.strip()
            
        except Exception as e:
            # Handle specific Gemini API errors with enhanced error messages
            error_message = str(e).lower()
            error_type = type(e).__name__
            
            # Check for quota/rate limit errors
            if any(keyword in error_message for keyword in ['quota', 'rate limit', 'too many requests', '429']):
                quota_type = "rate_limit" if any(kw in error_message for kw in ['rate limit', 'too many requests']) else "quota"
                raise QuotaExceededError(
                    f"Gemini API {quota_type} exceeded: {str(e)}",
                    api_name="Gemini API",
                    quota_type=quota_type
                )
            
            # Check for authentication errors
            if any(keyword in error_message for keyword in ['unauthorized', 'invalid api key', 'authentication', '401', '403']):
                raise APIError(
                    f"Gemini API authentication failed: {str(e)}. Verify your API key is valid and has necessary permissions.",
                    api_name="Gemini API",
                    details="Check your GEMINI_API_KEY environment variable"
                )
            
            # Check for video processing errors
            if any(keyword in error_message for keyword in ['video', 'unsupported', 'format', 'mime type']):
                raise APIError(
                    f"Gemini API could not process the video: {str(e)}",
                    api_name="Gemini API",
                    details=f"Video URL: {video_url}. The video format may not be supported or the video may be too long."
                )
            
            # Check for network/timeout errors
            if any(keyword in error_message for keyword in ['timeout', 'connection', 'network']):
                raise APIError(
                    f"Gemini API network error: {str(e)}",
                    api_name="Gemini API",
                    details=f"Video URL: {video_url}. Check your internet connection and try again."
                )
            
            # Check for content policy violations
            if any(keyword in error_message for keyword in ['safety', 'policy', 'blocked', 'filtered']):
                raise APIError(
                    f"Gemini API content policy violation: {str(e)}",
                    api_name="Gemini API",
                    details=f"Video URL: {video_url}. The video content may violate Gemini's safety policies."
                )
            
            # Generic API error with enhanced context
            raise APIError(
                f"Gemini API call failed: {str(e)}",
                api_name="Gemini API",
                details=f"Video URL: {video_url}, Error type: {error_type}, Model: gemini-2.0-flash-exp"
            )
    
    def _api_call_with_retry(self, api_func, *args, **kwargs):
        """
        Execute API call with retry logic and exponential backoff.
        
        This method implements a robust retry mechanism for API calls,
        with exponential backoff to handle temporary failures gracefully.
        It includes enhanced error categorization and informative error messages.
        
        Args:
            api_func: The API function to call
            *args: Arguments to pass to the API function
            **kwargs: Keyword arguments to pass to the API function
            
        Returns:
            The result of the API function call
            
        Raises:
            APIError: If all retry attempts fail
            QuotaExceededError: If quota is exceeded (no retry)
            VideoUnavailableError: If video is unavailable (no retry)
        """
        last_exception = None
        retry_count = 0
        
        for attempt in range(self.max_retries):
            try:
                return api_func(*args, **kwargs)
                
            except (QuotaExceededError, VideoUnavailableError):
                # Don't retry quota errors or video unavailable errors
                raise
                
            except APIError as e:
                last_exception = e
                retry_count = attempt + 1
                
                # Don't retry authentication errors or permanent failures
                if self._is_non_retryable_error(e):
                    raise self._enhance_error_message(e, retry_count, self.max_retries)
                
                # If this is the last attempt, raise the error with enhanced message
                if attempt == self.max_retries - 1:
                    raise self._enhance_error_message(e, retry_count, self.max_retries)
                
                # Calculate backoff time (exponential backoff with jitter)
                backoff_time = self._calculate_backoff_time(attempt)
                time.sleep(backoff_time)
                
            except Exception as e:
                # Convert unexpected errors to APIError
                last_exception = APIError(
                    f"Unexpected error during API call: {str(e)}",
                    api_name="Unknown",
                    details=f"Error type: {type(e).__name__}, Message: {str(e)}"
                )
                retry_count = attempt + 1
                
                if attempt == self.max_retries - 1:
                    raise self._enhance_error_message(last_exception, retry_count, self.max_retries)
                
                # Shorter backoff for unexpected errors
                backoff_time = min(2 ** attempt, 30)  # Cap at 30 seconds for unexpected errors
                time.sleep(backoff_time)
        
        # This should never be reached, but just in case
        if last_exception:
            raise self._enhance_error_message(last_exception, retry_count, self.max_retries)
        else:
            raise APIError(
                "All retry attempts failed with unknown error",
                api_name="Unknown",
                details=f"Max retries: {self.max_retries}, No exception captured"
            )
    
    def _is_non_retryable_error(self, error: APIError) -> bool:
        """
        Determine if an API error should not be retried.
        
        Args:
            error: The APIError to check
            
        Returns:
            bool: True if the error should not be retried
        """
        error_message = str(error).lower()
        
        # Authentication and authorization errors
        if any(keyword in error_message for keyword in [
            'authentication', 'unauthorized', 'invalid api key', 
            'api key', 'forbidden', 'access denied'
        ]):
            return True
        
        # Client errors that won't be fixed by retrying
        if any(keyword in error_message for keyword in [
            'bad request', 'invalid request', 'malformed',
            'not found', 'method not allowed'
        ]):
            return True
        
        # Video-specific permanent errors
        if any(keyword in error_message for keyword in [
            'video not found', 'video unavailable', 'private video',
            'deleted video', 'restricted video'
        ]):
            return True
        
        return False
    
    def _calculate_backoff_time(self, attempt: int) -> float:
        """
        Calculate backoff time for retry attempts using exponential backoff with jitter.
        
        Args:
            attempt: The current attempt number (0-based)
            
        Returns:
            float: Backoff time in seconds
        """
        # Base exponential backoff: 2^attempt seconds
        base_backoff = 2 ** attempt
        
        # Add jitter to prevent thundering herd problem
        jitter = time.time() % 1  # Random jitter between 0-1 seconds
        
        # Calculate total backoff time
        backoff_time = base_backoff + jitter
        
        # Cap the maximum backoff time to prevent excessive delays
        max_backoff = 60  # 60 seconds maximum
        
        return min(backoff_time, max_backoff)
    
    def _enhance_error_message(self, error: Exception, retry_count: int, max_retries: int) -> Exception:
        """
        Enhance error messages with retry information and helpful context.
        
        Args:
            error: The original error
            retry_count: Number of retry attempts made
            max_retries: Maximum number of retries configured
            
        Returns:
            Exception: Enhanced error with additional context
        """
        if isinstance(error, APIError):
            # Create enhanced error message
            enhanced_message = f"{error.message} (Failed after {retry_count}/{max_retries} attempts)"
            
            # Add helpful suggestions based on error type
            suggestions = self._get_error_suggestions(error)
            if suggestions:
                enhanced_message += f". Suggestions: {suggestions}"
            
            # Create new APIError with enhanced message
            enhanced_error = APIError(
                enhanced_message,
                api_name=error.api_name,
                status_code=getattr(error, 'status_code', None),
                details=error.details
            )
            
            return enhanced_error
        
        elif isinstance(error, QuotaExceededError):
            # Enhance quota error with helpful information
            enhanced_message = f"{error.message} (Quota limit reached)"
            
            if error.quota_type:
                enhanced_message += f" - Quota type: {error.quota_type}"
            
            enhanced_message += ". Try again later or check your API quota limits."
            
            enhanced_error = QuotaExceededError(
                enhanced_message,
                api_name=error.api_name,
                quota_type=error.quota_type,
                reset_time=getattr(error, 'reset_time', None)
            )
            
            return enhanced_error
        
        else:
            # For other error types, just add retry information
            enhanced_message = f"{str(error)} (Failed after {retry_count}/{max_retries} attempts)"
            error.args = (enhanced_message,)
            return error
    
    def _get_error_suggestions(self, error: APIError) -> str:
        """
        Get helpful suggestions based on the type of API error.
        
        Args:
            error: The APIError to analyze
            
        Returns:
            str: Helpful suggestions for resolving the error
        """
        error_message = str(error).lower()
        
        if 'api key' in error_message or 'authentication' in error_message:
            return "Check your API key configuration and ensure it's valid"
        
        elif 'quota' in error_message or 'rate limit' in error_message:
            return "Wait before retrying or check your API quota limits"
        
        elif 'network' in error_message or 'timeout' in error_message:
            return "Check your internet connection and try again"
        
        elif 'video' in error_message and 'unavailable' in error_message:
            return "The video may be private, deleted, or restricted"
        
        elif error.api_name == "YouTube Data API":
            return "Verify the video URL and your YouTube API configuration"
        
        elif error.api_name == "Gemini API":
            return "Check your Gemini API key and ensure the video is accessible"
        
        else:
            return "Check your configuration and try again"
    
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