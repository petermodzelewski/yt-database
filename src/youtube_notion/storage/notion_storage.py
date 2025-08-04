"""
Notion storage backend implementation.

This module provides a concrete implementation of the Storage interface
for storing video summaries in Notion databases.
"""

import time
from typing import Dict, Any, Optional
from notion_client import Client
from notion_client.errors import APIResponseError, RequestTimeoutError

from ..interfaces.storage import Storage
from ..utils.exceptions import StorageError, ConfigurationError, APIError
from ..utils.markdown_converter import (
    markdown_to_notion_blocks, 
    enrich_timestamps_with_links
)


class NotionStorage(Storage):
    """
    Storage backend implementation for Notion databases.
    
    This class handles storing video summaries in Notion databases with
    rich formatting, embedded videos, and clickable timestamps.
    """
    
    def __init__(self, notion_token: str, database_name: str, parent_page_name: str,
                 max_retries: int = 3, timeout_seconds: int = 30):
        """
        Initialize the Notion storage backend.
        
        Args:
            notion_token: Notion integration token
            database_name: Name of the target Notion database
            parent_page_name: Name of the parent page containing the database
            max_retries: Maximum number of retry attempts for API calls (default: 3)
            timeout_seconds: Timeout for API calls in seconds (default: 30)
            
        Raises:
            ConfigurationError: If configuration parameters are invalid
        """
        # Validate configuration parameters at initialization
        if not notion_token or not notion_token.strip():
            raise ConfigurationError("Notion token is required and cannot be empty")
        
        if not database_name or not database_name.strip():
            raise ConfigurationError("Database name is required and cannot be empty")
        
        if not parent_page_name or not parent_page_name.strip():
            raise ConfigurationError("Parent page name is required and cannot be empty")
        
        if max_retries < 0:
            raise ConfigurationError("Max retries must be non-negative")
        
        if timeout_seconds <= 0:
            raise ConfigurationError("Timeout seconds must be positive")
        
        self.notion_token = notion_token.strip()
        self.database_name = database_name.strip()
        self.parent_page_name = parent_page_name.strip()
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self._client = None
        self._database_id = None
    
    @property
    def client(self) -> Client:
        """Get or create the Notion client."""
        if self._client is None:
            if not self.notion_token:
                raise ConfigurationError("Notion token is required")
            self._client = Client(auth=self.notion_token, timeout_ms=self.timeout_seconds * 1000)
        return self._client
    
    def _api_call_with_retry(self, api_func, *args, **kwargs):
        """
        Execute Notion API call with retry logic and exponential backoff.
        
        Args:
            api_func: The API function to call
            *args: Arguments to pass to the API function
            **kwargs: Keyword arguments to pass to the API function
            
        Returns:
            The result of the API function call
            
        Raises:
            StorageError: If all retry attempts fail
            APIError: If API calls fail with non-retryable errors
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return api_func(*args, **kwargs)
                
            except APIResponseError as e:
                last_exception = e
                
                # Check if this is a non-retryable error
                if self._is_non_retryable_error(e):
                    raise self._convert_notion_error(e)
                
                # If this is the last attempt, raise the error
                if attempt == self.max_retries - 1:
                    raise self._convert_notion_error(e)
                
                # Calculate backoff time and wait
                backoff_time = self._calculate_backoff_time(attempt)
                time.sleep(backoff_time)
                
            except RequestTimeoutError as e:
                last_exception = e
                
                # If this is the last attempt, raise the error
                if attempt == self.max_retries - 1:
                    raise StorageError(
                        f"Notion API request timed out after {self.timeout_seconds}s",
                        details=f"Failed after {self.max_retries} attempts"
                    )
                
                # Calculate backoff time and wait
                backoff_time = self._calculate_backoff_time(attempt)
                time.sleep(backoff_time)
                
            except Exception as e:
                # For unexpected errors, don't retry
                raise StorageError(
                    f"Unexpected error during Notion API call: {str(e)}",
                    details=f"Error type: {type(e).__name__}"
                )
        
        # This should never be reached, but just in case
        if last_exception:
            raise self._convert_notion_error(last_exception)
        else:
            raise StorageError(
                "All retry attempts failed with unknown error",
                details=f"Max retries: {self.max_retries}"
            )
    
    def _is_non_retryable_error(self, error: APIResponseError) -> bool:
        """
        Determine if a Notion API error should not be retried.
        
        Args:
            error: The APIResponseError to check
            
        Returns:
            bool: True if the error should not be retried
        """
        # Authentication and authorization errors
        if error.status in [401, 403]:
            return True
        
        # Client errors that won't be fixed by retrying
        if error.status in [400, 404, 409, 422]:
            return True
        
        return False
    
    def _convert_notion_error(self, error: APIResponseError) -> Exception:
        """
        Convert Notion API errors to appropriate application exceptions.
        
        Args:
            error: The APIResponseError to convert
            
        Returns:
            Exception: Appropriate application exception
        """
        if error.status == 401:
            return ConfigurationError(
                f"Notion API authentication failed: {error.body}",
                details="Check that your Notion token is valid"
            )
        
        elif error.status == 403:
            return ConfigurationError(
                f"Notion API access forbidden: {error.body}",
                details="Check that your Notion integration has access to the database and page"
            )
        
        elif error.status == 404:
            return StorageError(
                f"Notion resource not found: {error.body}",
                details="The database or page may have been deleted or moved"
            )
        
        elif error.status == 409:
            return StorageError(
                f"Notion API conflict: {error.body}",
                details="The resource may have been modified by another process"
            )
        
        elif error.status == 422:
            return StorageError(
                f"Notion API validation error: {error.body}",
                details="The request data may be invalid or malformed"
            )
        
        elif error.status == 429:
            return APIError(
                f"Notion API rate limit exceeded: {error.body}",
                api_name="Notion API",
                status_code=error.status,
                details="Too many requests. Try again later."
            )
        
        elif error.status >= 500:
            return APIError(
                f"Notion API server error: {error.body}",
                api_name="Notion API",
                status_code=error.status,
                details="Notion service is experiencing issues. Try again later."
            )
        
        else:
            return StorageError(
                f"Notion API error: {error.body}",
                details=f"Status code: {error.status}"
            )
    
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
        max_backoff = 30  # 30 seconds maximum
        
        return min(backoff_time, max_backoff)
    
    def store_video_summary(self, video_data: Dict[str, Any]) -> bool:
        """
        Store processed video data in Notion database.
        
        Creates a page with:
        1. YouTube video embedded at the top
        2. A divider for visual separation
        3. The summary with timestamps converted to clickable YouTube links
        4. All content converted from markdown to formatted Notion blocks
        
        Args:
            video_data: Processed video data containing:
                - Title: Video title
                - Channel: Channel name
                - Video URL: Original YouTube URL
                - Cover: Thumbnail URL (optional)
                - Summary: Generated markdown summary
                
        Returns:
            bool: True if successful, False otherwise
            
        Raises:
            StorageError: If storage operation fails
            ConfigurationError: If storage backend is not properly configured
        """
        try:
            # Validate required fields
            required_fields = ['Title', 'Channel', 'Video URL', 'Summary']
            for field in required_fields:
                if field not in video_data:
                    raise StorageError(f"Missing required field: {field}")
            
            # Get database ID
            database_id = self.find_target_location()
            if not database_id:
                raise StorageError(
                    f"Could not find database '{self.database_name}' "
                    f"in parent page '{self.parent_page_name}'"
                )
            
            # Extract data
            title = video_data['Title']
            channel = video_data['Channel']
            video_url = video_data['Video URL']
            summary = video_data['Summary']
            cover_url = video_data.get('Cover')
            
            # Enrich timestamps in summary with YouTube links
            enriched_summary = enrich_timestamps_with_links(summary, video_url)
            
            # Convert enriched markdown summary to Notion blocks
            summary_blocks = markdown_to_notion_blocks(enriched_summary)
            
            # Create YouTube embed block
            youtube_embed = {
                "object": "block",
                "type": "embed",
                "embed": {
                    "url": video_url
                }
            }
            
            # Add a divider after the video for better visual separation
            divider = {
                "object": "block",
                "type": "divider",
                "divider": {}
            }
            
            # Combine embed, divider, and summary blocks
            all_blocks = [youtube_embed, divider] + summary_blocks
            
            # Create the page properties
            properties = {
                "Title": {
                    "title": [
                        {
                            "type": "text",
                            "text": {"content": title}
                        }
                    ]
                },
                "Video URL": {
                    "url": video_url
                },
                "Channel": {
                    "rich_text": [
                        {
                            "type": "text", 
                            "text": {"content": channel}
                        }
                    ]
                }
            }
            
            # Create the page with YouTube embed and summary blocks as content
            page = self._api_call_with_retry(
                self.client.pages.create,
                parent={"database_id": database_id},
                properties=properties,
                children=all_blocks,
                cover={"type": "external", "external": {"url": cover_url}} if cover_url else None
            )
            
            return True
            
        except Exception as e:
            if isinstance(e, (StorageError, ConfigurationError)):
                raise
            raise StorageError(f"Failed to store video summary: {str(e)}", details=str(e))
    
    def validate_configuration(self) -> bool:
        """
        Validate that the storage backend is properly configured.
        
        Returns:
            bool: True if configuration is valid, False otherwise
            
        Raises:
            ConfigurationError: If configuration validation fails
        """
        try:
            # Check required configuration
            if not self.notion_token:
                raise ConfigurationError("Notion token is required")
            if not self.database_name:
                raise ConfigurationError("Database name is required")
            if not self.parent_page_name:
                raise ConfigurationError("Parent page name is required")
            
            # Test Notion client connection
            try:
                # Try to create client and make a simple API call
                client = Client(auth=self.notion_token, timeout_ms=self.timeout_seconds * 1000)
                # Test with a simple search to validate the token
                self._api_call_with_retry(
                    client.search,
                    filter={"property": "object", "value": "database"}
                )
                return True
            except (ConfigurationError, APIError):
                # Re-raise configuration and API errors as-is
                raise
            except Exception as e:
                raise ConfigurationError(
                    f"Invalid Notion configuration: {str(e)}",
                    details="Check that your Notion token is valid and has proper permissions"
                )
                
        except ConfigurationError:
            raise
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {str(e)}")
    
    def find_target_location(self) -> Optional[str]:
        """
        Find and return the target Notion database ID.
        
        Returns:
            Optional[str]: Database ID if found, None otherwise
            
        Raises:
            StorageError: If location discovery fails
            ConfigurationError: If storage backend is not properly configured
        """
        try:
            # Use cached database ID if available
            if self._database_id:
                return self._database_id
            
            # Search for databases
            databases = self._api_call_with_retry(
                self.client.search,
                filter={"property": "object", "value": "database"}
            )
            
            for db in databases['results']:
                db_title = db['title'][0]['plain_text'] if db['title'] else ''
                
                if db_title == self.database_name:
                    if self.parent_page_name:
                        # Check if database is in the correct parent page
                        try:
                            parent = self._api_call_with_retry(
                                self.client.pages.retrieve,
                                db['parent']['page_id']
                            )
                            parent_title = ''
                            if parent['properties'].get('title', {}).get('title'):
                                parent_title = parent['properties']['title']['title'][0]['plain_text']
                            
                            if parent_title == self.parent_page_name:
                                self._database_id = db['id']
                                return self._database_id
                        except Exception:
                            # If we can't retrieve parent info, skip this database
                            continue
                    else:
                        # No parent page requirement, use first match
                        self._database_id = db['id']
                        return self._database_id
            
            return None
            
        except Exception as e:
            if isinstance(e, (StorageError, ConfigurationError)):
                raise
            raise StorageError(f"Failed to find target database: {str(e)}", details=str(e))