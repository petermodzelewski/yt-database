"""
Gemini AI implementation of the SummaryWriter interface.

This module provides a concrete implementation of the SummaryWriter interface
using Google's Gemini AI for generating video summaries with streaming support,
retry logic, and comprehensive error handling.
"""

import os
import re
import time
import json
from typing import Dict, Any, Optional
import google.genai as genai
from google.genai import types

from ..interfaces.summary_writer import SummaryWriter
from ..utils.chat_logger import ChatLogger
from ..utils.exceptions import (
    SummaryGenerationError,
    ConfigurationError,
    APIError,
    QuotaExceededError
)
from ..config.constants import DEFAULT_SUMMARY_PROMPT, MAX_VIDEO_DURATION_SECONDS
from ..utils.video_utils import calculate_video_splits


class GeminiSummaryWriter(SummaryWriter):
    """
    Summary writer implementation using Google Gemini AI.
    
    This class implements the SummaryWriter interface to generate AI-powered
    video summaries using Google's Gemini API. It includes streaming response
    handling, retry logic, conversation logging, and comprehensive error handling.
    """
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp",
                 temperature: float = 0.1, max_output_tokens: int = 4000,
                 default_prompt: str = DEFAULT_SUMMARY_PROMPT,
                 max_retries: int = 3, timeout_seconds: int = 120,
                 chat_logger: Optional[ChatLogger] = None):
        """
        Initialize the Gemini summary writer.
        
        Args:
            api_key: Google Gemini API key
            model: Gemini model to use (default: "gemini-2.0-flash-exp")
            temperature: AI temperature 0-2 (default: 0.1)
            max_output_tokens: Maximum output tokens (default: 4000)
            default_prompt: Default prompt for summary generation
            max_retries: Maximum number of retry attempts (default: 3)
            timeout_seconds: Timeout for API calls in seconds (default: 120)
            chat_logger: Optional chat logger instance (creates new if None)
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not api_key:
            raise ConfigurationError("Gemini API key is required")
        
        if temperature < 0 or temperature > 2:
            raise ConfigurationError("Temperature must be between 0 and 2")
        
        if max_output_tokens <= 0:
            raise ConfigurationError("Max output tokens must be positive")
        
        if max_retries < 0:
            raise ConfigurationError("Max retries must be non-negative")
        
        if timeout_seconds <= 0:
            raise ConfigurationError("Timeout seconds must be positive")
        
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.default_prompt = default_prompt
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        
        # Initialize chat logger
        self.chat_logger = chat_logger or ChatLogger()
    
    def generate_summary(self, video_url: str, video_metadata: Dict[str, Any],
                         custom_prompt: Optional[str] = None) -> str:
        """
        Generate a markdown summary for the video using Gemini AI.
        
        Args:
            video_url: YouTube URL to process
            video_metadata: Video metadata (title, channel, description, etc.)
            custom_prompt: Optional custom prompt for generation
            
        Returns:
            str: Markdown summary with timestamps and rich formatting
            
        Raises:
            SummaryGenerationError: If summary generation fails
            ConfigurationError: If the writer is not properly configured
        """
        if not video_url:
            raise SummaryGenerationError("Video URL is required")

        if not video_metadata:
            raise SummaryGenerationError("Video metadata is required")

        prompt = custom_prompt or self.default_prompt
        duration_seconds = video_metadata.get('duration', 0)

        try:
            if duration_seconds > MAX_VIDEO_DURATION_SECONDS:
                response = self._generate_summary_for_long_video(video_url, video_metadata, prompt)
            else:
                response = self._api_call_with_retry(self._call_gemini_api, video_url, prompt)

            # Log the chat conversation
            try:
                video_id = video_metadata.get('video_id', 'unknown')
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

        except (APIError, QuotaExceededError):
            # Re-raise known API errors as SummaryGenerationError
            raise
        except Exception as e:
            # Wrap unexpected errors
            raise SummaryGenerationError(
                f"Unexpected error during summary generation: {str(e)}",
                details=f"Video URL: {video_url}, Error type: {type(e).__name__}"
            )

    def _generate_summary_for_long_video(self, video_url: str, video_metadata: Dict[str, Any], prompt: str) -> str:
        """
        Generate a summary for a long video by splitting it into chunks and processing them sequentially.
        """
        duration_seconds = video_metadata.get('duration', 0)
        splits = calculate_video_splits(duration_seconds)

        full_summary = ""
        for i, (start, end) in enumerate(splits):
            print(f"Processing video chunk {i+1}/{len(splits)}: {start}s - {end}s")

            if i == 0:
                chunk_prompt = f"This is the first part of a video. {prompt}"
            else:
                chunk_prompt = (
                    f"This is part {i+1} of {len(splits)} of a video, starting from timestamp {start}s.\n"
                    f"The summary from the previous part is:\n<summary>{full_summary}</summary>\n"
                    f"Your task is to write a summary for the second part with timestamps according to the instructions.\n"
                    f"<instruction>{prompt}</instruction>\n"
                    f"<important>Return only the continuation of the summary, don't duplicate content from parts already in the previous summary.</important>"
                )

            summary_part = self._api_call_with_retry(
                self._call_gemini_api,
                video_url,
                chunk_prompt,
                start_offset=f"{start}s",
                end_offset=f"{end}s"
            )

            # Log the chat for the current chunk
            try:
                video_id = video_metadata.get('video_id', 'unknown')
                self.chat_logger.log_chat_chunk(
                    video_id=video_id,
                    video_url=video_url,
                    prompt=chunk_prompt,
                    response=summary_part,
                    video_metadata=video_metadata,
                    chunk_index=i,
                    start_offset=start,
                    end_offset=end
                )
            except Exception as e:
                print(f"Warning: Failed to log chat conversation for chunk {i}: {e}")

            full_summary += "\n" + summary_part if full_summary else summary_part

        return full_summary
    
    def validate_configuration(self) -> bool:
        """
        Validate that the summary writer is properly configured.
        
        Returns:
            bool: True if configuration is valid, False otherwise
            
        Raises:
            ConfigurationError: If configuration validation fails
        """
        try:
            # Check API key
            if not self.api_key:
                raise ConfigurationError("Gemini API key is not set")
            
            # Validate configuration parameters
            if self.temperature < 0 or self.temperature > 2:
                raise ConfigurationError("Temperature must be between 0 and 2")
            
            if self.max_output_tokens <= 0:
                raise ConfigurationError("Max output tokens must be positive")
            
            if self.max_retries < 0:
                raise ConfigurationError("Max retries must be non-negative")
            
            if self.timeout_seconds <= 0:
                raise ConfigurationError("Timeout seconds must be positive")
            
            # Test API key by creating a client (doesn't make actual API call)
            try:
                genai.Client(api_key=self.api_key)
            except Exception as e:
                raise ConfigurationError(
                    f"Invalid Gemini API key or client initialization failed: {str(e)}"
                )
            
            return True
            
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(
                f"Configuration validation failed: {str(e)}"
            )
    
    def _call_gemini_api(self, video_url: str, prompt: str,
                         start_offset: Optional[str] = None, end_offset: Optional[str] = None) -> str:
        """
        Make the actual Gemini API call with streaming response handling.
        
        Args:
            video_url: YouTube URL for Gemini to process
            prompt: Prompt for summary generation
            start_offset: Start offset for video chunk
            end_offset: End offset for video chunk
            
        Returns:
            str: AI-generated markdown summary with timestamps
            
        Raises:
            APIError: If Gemini API call fails
            QuotaExceededError: If API quota is exceeded
        """
        try:
            # Initialize Gemini client
            client = genai.Client(api_key=self.api_key)
            
            # Prepare video part
            video_part = types.Part(
                file_data=types.FileData(
                    file_uri=video_url,
                    mime_type="video/*"
                )
            )
            if start_offset and end_offset:
                video_part.video_metadata = types.VideoMetadata(
                    start_offset=start_offset,
                    end_offset=end_offset
                )

            # Prepare content for the API call
            contents = [
                types.Content(
                    role="user",
                    parts=[video_part, types.Part.from_text(text=prompt)]
                )
            ]
            
            # Configure generation settings
            generate_content_config = types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                response_mime_type="text/plain"
            )
            
            # Stream response and collect full text
            full_response = ""
            
            try:
                for chunk in client.models.generate_content_stream(
                    model=self.model,
                    contents=contents,
                    config=generate_content_config
                ):
                    if chunk.text:
                        full_response += chunk.text
            
            except Exception as stream_error:
                # If streaming fails, try non-streaming approach
                response = client.models.generate_content(
                    model=self.model,
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
                
                # Parse retry delay from error response if available
                retry_delay_seconds = self._parse_retry_delay_from_error(str(e))
                
                raise QuotaExceededError(
                    f"Gemini API {quota_type} exceeded: {str(e)}",
                    api_name="Gemini API",
                    quota_type=quota_type,
                    retry_delay_seconds=retry_delay_seconds,
                    raw_error=str(e)
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
                details=f"Video URL: {video_url}, Error type: {error_type}, Model: {self.model}"
            )

    def _call_gemini_api_for_text(self, prompt: str) -> str:
        """
        Make a Gemini API call for text-only input.
        """
        try:
            client = genai.Client(api_key=self.api_key)
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
            generate_content_config = types.GenerateContentConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_output_tokens,
                response_mime_type="text/plain"
            )
            response = client.models.generate_content(
                model=self.model,
                contents=contents,
                config=generate_content_config
            )
            return response.text.strip() if response.text else ""
        except Exception as e:
            raise APIError(f"Gemini API text call failed: {str(e)}", api_name="Gemini API")
    
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
            QuotaExceededError: If quota is exceeded (with retry logic)
        """
        last_exception = None
        retry_count = 0
        
        for attempt in range(self.max_retries):
            try:
                return api_func(*args, **kwargs)
                
            except QuotaExceededError as e:
                # Handle quota errors with retry delay
                if e.retry_delay_seconds is not None and attempt < self.max_retries - 1:
                    # Wait for the specified retry delay + 15 seconds buffer
                    # In test mode, cap the retry delay to avoid long test hangs
                    base_delay = e.retry_delay_seconds + 15
                    
                    # Check if we're in test mode (common test environment variables)
                    is_test_mode = any(var in os.environ for var in ['PYTEST_CURRENT_TEST', 'TESTING', '_PYTEST_RAISE'])
                    
                    if is_test_mode:
                        # In test mode, cap retry delay to 5 seconds maximum
                        retry_delay = min(base_delay, 5)
                        print(f"API quota exceeded. Test mode: waiting {retry_delay}s (capped from {base_delay}s) before retry (attempt {attempt + 1}/{self.max_retries})...")
                    else:
                        retry_delay = base_delay
                        print(f"API quota exceeded. Waiting {retry_delay} seconds before retry (attempt {attempt + 1}/{self.max_retries})...")
                    
                    time.sleep(retry_delay)
                    continue
                else:
                    # No retry delay specified or max retries reached
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
                    api_name="Gemini API",
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
                api_name="Gemini API",
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
        if isinstance(error, QuotaExceededError):
            # Enhance quota error with helpful information (check this first since it inherits from APIError)
            enhanced_message = f"{error.message} (Failed after {retry_count}/{max_retries} attempts)"
            
            if error.quota_type:
                enhanced_message += f" - Quota type: {error.quota_type}"
            
            if error.retry_delay_seconds:
                enhanced_message += f" - Retry after: {error.retry_delay_seconds + 15}s (including buffer)"
            else:
                enhanced_message += ". Try again later or check your API quota limits."
            
            enhanced_error = QuotaExceededError(
                enhanced_message,
                api_name=error.api_name,
                quota_type=error.quota_type,
                reset_time=getattr(error, 'reset_time', None),
                retry_delay_seconds=error.retry_delay_seconds,
                raw_error=getattr(error, 'raw_error', None)
            )
            
            return enhanced_error
        
        elif isinstance(error, APIError):
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
        
        elif error.api_name == "Gemini API":
            return "Check your Gemini API key and ensure the video is accessible"
        
        else:
            return "Check your configuration and try again"
    
    def _parse_retry_delay_from_error(self, error_str: str) -> Optional[int]:
        """
        Parse retry delay from Gemini API error response.
        
        The Gemini API includes retry delay information in quota exceeded errors:
        'retryDelay': '18s' in the error details.
        
        Args:
            error_str: String representation of the error
            
        Returns:
            int: Retry delay in seconds, or None if not found
        """
        try:
            # Look for retryDelay pattern in the error string
            # Pattern: 'retryDelay': '18s' or "retryDelay": "18s"
            retry_delay_match = re.search(r"['\"]retryDelay['\"]:\s*['\"](\d+)s['\"]", error_str)
            
            if retry_delay_match:
                return int(retry_delay_match.group(1))
            
            # Alternative pattern: retryDelay: 18s (without quotes)
            retry_delay_match = re.search(r"retryDelay:\s*(\d+)s", error_str)
            
            if retry_delay_match:
                return int(retry_delay_match.group(1))
            
            # Try to parse as JSON if the error contains structured data
            if '{' in error_str and '}' in error_str:
                # Extract JSON-like structures from the error string
                json_matches = re.findall(r'\{[^{}]*\}', error_str)
                for json_str in json_matches:
                    try:
                        parsed = json.loads(json_str.replace("'", '"'))
                        if 'retryDelay' in parsed:
                            delay_str = parsed['retryDelay']
                            if delay_str.endswith('s'):
                                return int(delay_str[:-1])
                    except (json.JSONDecodeError, ValueError, KeyError):
                        continue
            
            return None
            
        except Exception:
            # If parsing fails, return None to fall back to default retry logic
            return None