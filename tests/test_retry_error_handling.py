"""
Comprehensive tests for retry logic and error handling in YouTube processing.

This module contains detailed tests for the enhanced retry mechanisms,
error categorization, and informative error messages implemented in
the YouTubeProcessor class.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from googleapiclient.errors import HttpError
import requests

from src.youtube_notion.processors.youtube_processor import YouTubeProcessor
from src.youtube_notion.processors.exceptions import (
    YouTubeProcessingError,
    InvalidURLError,
    APIError,
    VideoUnavailableError,
    QuotaExceededError
)


class TestRetryLogicEnhancements:
    """Test cases for enhanced retry logic."""
    
    @pytest.fixture
    def processor(self):
        """Create a YouTubeProcessor instance for testing."""
        return YouTubeProcessor.from_api_keys(
            gemini_api_key="test_gemini_key",
            youtube_api_key="test_youtube_key",
            max_retries=3,
            timeout_seconds=30
        )
    
    @patch('src.youtube_notion.processors.youtube_processor.time.sleep')
    def test_retry_with_exponential_backoff_and_jitter(self, mock_sleep, processor):
        """Test that retry uses exponential backoff with jitter."""
        mock_func = Mock()
        mock_func.side_effect = [
            APIError("Temporary error 1", api_name="Test API"),
            APIError("Temporary error 2", api_name="Test API"),
            "Success on third try"
        ]
        
        with patch('src.youtube_notion.processors.youtube_processor.time.time', return_value=0.5):
            result = processor._api_call_with_retry(mock_func)
        
        assert result == "Success on third try"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2
        
        # Verify exponential backoff with jitter
        sleep_calls = mock_sleep.call_args_list
        
        # First backoff: 2^0 + 0.5 = 1.5 seconds
        assert sleep_calls[0][0][0] == 1.5
        
        # Second backoff: 2^1 + 0.5 = 2.5 seconds
        assert sleep_calls[1][0][0] == 2.5
    
    @patch('src.youtube_notion.processors.youtube_processor.time.sleep')
    def test_retry_backoff_capped_at_maximum(self, mock_sleep, processor):
        """Test that backoff time is capped at maximum value."""
        # Set high max_retries to test backoff capping
        processor.max_retries = 10
        
        mock_func = Mock()
        mock_func.side_effect = [APIError("Error", api_name="Test API")] * 10
        
        with patch('src.youtube_notion.processors.youtube_processor.time.time', return_value=0.0):
            with pytest.raises(APIError):
                processor._api_call_with_retry(mock_func)
        
        # Check that later backoff times are capped at 60 seconds
        sleep_calls = mock_sleep.call_args_list
        
        # Later attempts should be capped at 60 seconds
        for call in sleep_calls[-3:]:  # Check last 3 calls
            assert call[0][0] <= 60
    
    @patch('src.youtube_notion.processors.youtube_processor.time.sleep')
    def test_non_retryable_errors_not_retried(self, mock_sleep, processor):
        """Test that non-retryable errors are not retried."""
        non_retryable_errors = [
            APIError("Invalid API key", api_name="Test API"),
            APIError("Authentication failed", api_name="Test API"),
            APIError("Unauthorized access", api_name="Test API"),
            APIError("Bad request format", api_name="Test API"),
            APIError("Video not found", api_name="Test API"),
            APIError("Method not allowed", api_name="Test API"),
        ]
        
        for error in non_retryable_errors:
            mock_func = Mock(side_effect=error)
            
            with pytest.raises(APIError):
                processor._api_call_with_retry(mock_func)
            
            # Should not retry
            assert mock_func.call_count == 1
            mock_sleep.assert_not_called()
            
            # Reset mocks for next iteration
            mock_func.reset_mock()
            mock_sleep.reset_mock()
    
    @patch('src.youtube_notion.processors.youtube_processor.time.sleep')
    def test_quota_errors_not_retried(self, mock_sleep, processor):
        """Test that quota exceeded errors are not retried."""
        mock_func = Mock()
        mock_func.side_effect = QuotaExceededError("Quota exceeded", api_name="Test API")
        
        with pytest.raises(QuotaExceededError):
            processor._api_call_with_retry(mock_func)
        
        assert mock_func.call_count == 1
        mock_sleep.assert_not_called()
    
    @patch('src.youtube_notion.processors.youtube_processor.time.sleep')
    def test_video_unavailable_errors_not_retried(self, mock_sleep, processor):
        """Test that video unavailable errors are not retried."""
        mock_func = Mock()
        mock_func.side_effect = VideoUnavailableError("Video unavailable", video_id="test_id")
        
        with pytest.raises(VideoUnavailableError):
            processor._api_call_with_retry(mock_func)
        
        assert mock_func.call_count == 1
        mock_sleep.assert_not_called()
    
    @patch('src.youtube_notion.processors.youtube_processor.time.sleep')
    def test_enhanced_error_messages_with_retry_info(self, mock_sleep, processor):
        """Test that error messages are enhanced with retry information."""
        mock_func = Mock()
        original_error = APIError("Original error message", api_name="Test API")
        mock_func.side_effect = original_error
        
        with pytest.raises(APIError) as exc_info:
            processor._api_call_with_retry(mock_func)
        
        # Error message should include retry information
        error_message = str(exc_info.value)
        assert "Failed after 3/3 attempts" in error_message
        assert "Original error message" in error_message
    
    @patch('src.youtube_notion.processors.youtube_processor.time.sleep')
    def test_error_suggestions_added_to_messages(self, mock_sleep, processor):
        """Test that helpful suggestions are added to error messages."""
        test_cases = [
            (APIError("Invalid API key", api_name="Test API"), "Check your API key configuration"),
            (APIError("Network timeout", api_name="Test API"), "Check your internet connection"),
            (APIError("Video unavailable", api_name="YouTube Data API"), "private, deleted, or restricted"),
        ]
        
        for original_error, expected_suggestion in test_cases:
            mock_func = Mock(side_effect=original_error)
            
            with pytest.raises(APIError) as exc_info:
                processor._api_call_with_retry(mock_func)
            
            error_message = str(exc_info.value)
            assert expected_suggestion in error_message
            
            mock_func.reset_mock()


class TestYouTubeAPIErrorHandling:
    """Test cases for YouTube Data API error handling."""
    
    @pytest.fixture
    def processor(self):
        """Create a YouTubeProcessor instance for testing."""
        return YouTubeProcessor.from_api_keys(gemini_api_key="test_gemini_key", youtube_api_key="test_youtube_key")
    
    def test_youtube_api_quota_exceeded_error(self, processor):
        """Test handling of YouTube API quota exceeded errors."""
        # Mock HttpError for quota exceeded
        mock_response = Mock()
        mock_response.status = 403
        
        http_error = HttpError(
            resp=mock_response,
            content=b'{"error": {"errors": [{"reason": "quotaExceeded", "message": "Quota exceeded"}]}}',
            uri="test_uri"
        )
        http_error.error_details = [{"reason": "quotaExceeded", "message": "Quota exceeded"}]
        
        with patch('src.youtube_notion.processors.youtube_processor.build') as mock_build:
            mock_youtube = Mock()
            mock_build.return_value = mock_youtube
            mock_youtube.videos().list().execute.side_effect = http_error
            
            with pytest.raises(QuotaExceededError) as exc_info:
                processor._get_metadata_via_api("test_video_id")
            
            assert "YouTube API quota exceeded" in str(exc_info.value)
            assert exc_info.value.api_name == "YouTube Data API"
            assert exc_info.value.quota_type == "per_minute"
    
    def test_youtube_api_rate_limit_error(self, processor):
        """Test handling of YouTube API rate limit errors."""
        # Mock HttpError for rate limiting
        mock_response = Mock()
        mock_response.status = 429
        
        http_error = HttpError(
            resp=mock_response,
            content=b'{"error": {"message": "Rate limit exceeded"}}',
            uri="test_uri"
        )
        http_error.error_details = [{"message": "Rate limit exceeded"}]
        
        with patch('src.youtube_notion.processors.youtube_processor.build') as mock_build:
            mock_youtube = Mock()
            mock_build.return_value = mock_youtube
            mock_youtube.videos().list().execute.side_effect = http_error
            
            with pytest.raises(QuotaExceededError) as exc_info:
                processor._get_metadata_via_api("test_video_id")
            
            assert "rate limit exceeded" in str(exc_info.value).lower()
            assert exc_info.value.quota_type == "rate_limit"
    
    def test_youtube_api_authentication_error(self, processor):
        """Test handling of YouTube API authentication errors."""
        # Mock HttpError for authentication failure
        mock_response = Mock()
        mock_response.status = 401
        
        http_error = HttpError(
            resp=mock_response,
            content=b'{"error": {"message": "Invalid API key"}}',
            uri="test_uri"
        )
        http_error.error_details = [{"message": "Invalid API key"}]
        
        with patch('src.youtube_notion.processors.youtube_processor.build') as mock_build:
            mock_youtube = Mock()
            mock_build.return_value = mock_youtube
            mock_youtube.videos().list().execute.side_effect = http_error
            
            with pytest.raises(APIError) as exc_info:
                processor._get_metadata_via_api("test_video_id")
            
            assert "authentication failed" in str(exc_info.value).lower()
            assert "Check your API key" in str(exc_info.value)
    
    def test_youtube_api_video_not_found_error(self, processor):
        """Test handling of video not found errors."""
        # Mock HttpError for not found
        mock_response = Mock()
        mock_response.status = 404
        
        http_error = HttpError(
            resp=mock_response,
            content=b'{"error": {"message": "Video not found"}}',
            uri="test_uri"
        )
        http_error.error_details = [{"message": "Video not found"}]
        
        with patch('src.youtube_notion.processors.youtube_processor.build') as mock_build:
            mock_youtube = Mock()
            mock_build.return_value = mock_youtube
            mock_youtube.videos().list().execute.side_effect = http_error
            
            with pytest.raises(VideoUnavailableError) as exc_info:
                processor._get_metadata_via_api("test_video_id")
            
            assert "Video not found" in str(exc_info.value)
            assert exc_info.value.video_id == "test_video_id"


class TestWebScrapingErrorHandling:
    """Test cases for web scraping error handling."""
    
    @pytest.fixture
    def processor(self):
        """Create a YouTubeProcessor instance without YouTube API key."""
        return YouTubeProcessor.from_api_keys(gemini_api_key="test_gemini_key")
    
    @patch('src.youtube_notion.processors.youtube_processor.requests.get')
    def test_web_scraping_timeout_error(self, mock_get, processor):
        """Test handling of timeout errors during web scraping."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        with pytest.raises(APIError) as exc_info:
            processor._get_metadata_via_scraping("test_video_id")
        
        error_message = str(exc_info.value)
        assert "Request timed out" in error_message
        assert "check network connection" in error_message
        assert exc_info.value.api_name == "Web Scraping"
    
    @patch('src.youtube_notion.processors.youtube_processor.requests.get')
    def test_web_scraping_connection_error(self, mock_get, processor):
        """Test handling of connection errors during web scraping."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(APIError) as exc_info:
            processor._get_metadata_via_scraping("test_video_id")
        
        error_message = str(exc_info.value)
        assert "Connection error" in error_message
        assert "Check your internet connection" in error_message
    
    @patch('src.youtube_notion.processors.youtube_processor.requests.get')
    def test_web_scraping_http_error_429(self, mock_get, processor):
        """Test handling of HTTP 429 (rate limiting) during web scraping."""
        mock_response = Mock()
        mock_response.status_code = 429
        http_error = requests.exceptions.HTTPError("429 Too Many Requests")
        http_error.response = mock_response
        mock_get.side_effect = http_error
        
        with pytest.raises(APIError) as exc_info:
            processor._get_metadata_via_scraping("test_video_id")
        
        error_message = str(exc_info.value)
        assert "HTTP error 429" in error_message
        assert "rate limiting" in error_message
    
    @patch('src.youtube_notion.processors.youtube_processor.requests.get')
    def test_web_scraping_http_error_403_404(self, mock_get, processor):
        """Test handling of HTTP 403/404 errors during web scraping."""
        for status_code in [403, 404]:
            mock_response = Mock()
            mock_response.status_code = status_code
            http_error = requests.exceptions.HTTPError(f"{status_code} Error")
            http_error.response = mock_response
            mock_get.side_effect = http_error
            
            with pytest.raises(APIError) as exc_info:
                processor._get_metadata_via_scraping("test_video_id")
            
            error_message = str(exc_info.value)
            assert f"HTTP error {status_code}" in error_message
            assert "private, deleted, or restricted" in error_message
            
            mock_get.reset_mock()


class TestGeminiAPIErrorHandling:
    """Test cases for Gemini API error handling."""
    
    @pytest.fixture
    def processor(self):
        """Create a YouTubeProcessor instance for testing."""
        return YouTubeProcessor.from_api_keys(gemini_api_key="test_gemini_key")
    
    def test_gemini_quota_exceeded_error(self, processor):
        """Test handling of Gemini API quota exceeded errors."""
        # Test the error handling directly through the _call_gemini_api method
        with patch('src.youtube_notion.processors.youtube_processor.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock quota exceeded error for both streaming and non-streaming
            mock_client.models.generate_content_stream.side_effect = Exception("Quota exceeded for requests")
            mock_client.models.generate_content.side_effect = Exception("Quota exceeded for requests")
            
            with pytest.raises(QuotaExceededError) as exc_info:
                processor._call_gemini_api("https://youtube.com/watch?v=test", "test prompt")
            
            assert "Gemini API quota exceeded" in str(exc_info.value)
            assert exc_info.value.api_name == "Gemini API"
            assert exc_info.value.quota_type == "quota"
    
    def test_gemini_rate_limit_error(self, processor):
        """Test handling of Gemini API rate limit errors."""
        with patch('src.youtube_notion.processors.youtube_processor.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock rate limit error for both streaming and non-streaming
            mock_client.models.generate_content_stream.side_effect = Exception("Rate limit exceeded")
            mock_client.models.generate_content.side_effect = Exception("Rate limit exceeded")
            
            with pytest.raises(QuotaExceededError) as exc_info:
                processor._call_gemini_api("https://youtube.com/watch?v=test", "test prompt")
            
            assert "rate_limit exceeded" in str(exc_info.value).lower()
            assert exc_info.value.quota_type == "rate_limit"
    
    def test_gemini_authentication_error(self, processor):
        """Test handling of Gemini API authentication errors."""
        with patch('src.youtube_notion.processors.youtube_processor.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock authentication error for both streaming and non-streaming
            mock_client.models.generate_content_stream.side_effect = Exception("Invalid API key provided")
            mock_client.models.generate_content.side_effect = Exception("Invalid API key provided")
            
            with pytest.raises(APIError) as exc_info:
                processor._call_gemini_api("https://youtube.com/watch?v=test", "test prompt")
            
            error_message = str(exc_info.value)
            assert "authentication failed" in error_message.lower()
            assert "Verify your API key" in error_message
            assert "GEMINI_API_KEY" in error_message
    
    def test_gemini_video_processing_error(self, processor):
        """Test handling of Gemini video processing errors."""
        with patch('src.youtube_notion.processors.youtube_processor.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock video processing error for both streaming and non-streaming
            mock_client.models.generate_content_stream.side_effect = Exception("Unsupported video format")
            mock_client.models.generate_content.side_effect = Exception("Unsupported video format")
            
            with pytest.raises(APIError) as exc_info:
                processor._call_gemini_api("https://youtube.com/watch?v=test", "test prompt")
            
            error_message = str(exc_info.value)
            assert "could not process the video" in error_message.lower()
            assert "format may not be supported" in error_message
    
    def test_gemini_content_policy_error(self, processor):
        """Test handling of Gemini content policy violations."""
        with patch('src.youtube_notion.processors.youtube_processor.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock content policy error for both streaming and non-streaming
            mock_client.models.generate_content_stream.side_effect = Exception("Content blocked by safety filters")
            mock_client.models.generate_content.side_effect = Exception("Content blocked by safety filters")
            
            with pytest.raises(APIError) as exc_info:
                processor._call_gemini_api("https://youtube.com/watch?v=test", "test prompt")
            
            error_message = str(exc_info.value)
            assert "content policy violation" in error_message.lower()
            assert "safety policies" in error_message
    
    def test_gemini_network_error(self, processor):
        """Test handling of Gemini network errors."""
        with patch('src.youtube_notion.processors.youtube_processor.genai.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            # Mock network error for both streaming and non-streaming
            mock_client.models.generate_content_stream.side_effect = Exception("Connection timeout")
            mock_client.models.generate_content.side_effect = Exception("Connection timeout")
            
            with pytest.raises(APIError) as exc_info:
                processor._call_gemini_api("https://youtube.com/watch?v=test", "test prompt")
            
            error_message = str(exc_info.value)
            assert "network error" in error_message.lower()
            assert "Check your internet connection" in error_message


class TestErrorMessageEnhancements:
    """Test cases for error message enhancements and suggestions."""
    
    @pytest.fixture
    def processor(self):
        """Create a YouTubeProcessor instance for testing."""
        return YouTubeProcessor.from_api_keys(gemini_api_key="test_gemini_key")
    
    def test_error_suggestions_for_api_key_errors(self, processor):
        """Test that API key errors get helpful suggestions."""
        error = APIError("Invalid API key", api_name="Test API")
        suggestions = processor._get_error_suggestions(error)
        
        assert "Check your API key configuration" in suggestions
    
    def test_error_suggestions_for_quota_errors(self, processor):
        """Test that quota errors get helpful suggestions."""
        error = APIError("Quota exceeded", api_name="Test API")
        suggestions = processor._get_error_suggestions(error)
        
        assert "Wait before retrying" in suggestions or "check your API quota limits" in suggestions
    
    def test_error_suggestions_for_network_errors(self, processor):
        """Test that network errors get helpful suggestions."""
        error = APIError("Network timeout", api_name="Test API")
        suggestions = processor._get_error_suggestions(error)
        
        assert "Check your internet connection" in suggestions
    
    def test_error_suggestions_for_video_errors(self, processor):
        """Test that video unavailable errors get helpful suggestions."""
        error = APIError("Video unavailable", api_name="YouTube Data API")
        suggestions = processor._get_error_suggestions(error)
        
        assert "private, deleted, or restricted" in suggestions
    
    def test_api_specific_suggestions(self, processor):
        """Test that API-specific suggestions are provided."""
        youtube_error = APIError("Some error", api_name="YouTube Data API")
        youtube_suggestions = processor._get_error_suggestions(youtube_error)
        assert "YouTube API configuration" in youtube_suggestions
        
        gemini_error = APIError("Some error", api_name="Gemini API")
        gemini_suggestions = processor._get_error_suggestions(gemini_error)
        assert "Gemini API key" in gemini_suggestions
    
    def test_enhanced_quota_error_messages(self, processor):
        """Test that quota errors are enhanced with helpful information."""
        original_error = QuotaExceededError(
            "Quota exceeded",
            api_name="Test API",
            quota_type="daily"
        )
        
        enhanced_error = processor._enhance_error_message(original_error, 2, 3)
        
        error_message = str(enhanced_error)
        assert "Failed after 2/3 attempts" in error_message
        assert "Wait before retrying" in error_message
    
    def test_enhanced_api_error_messages(self, processor):
        """Test that API errors are enhanced with retry information."""
        original_error = APIError("Original message", api_name="Test API")
        
        enhanced_error = processor._enhance_error_message(original_error, 3, 3)
        
        error_message = str(enhanced_error)
        assert "Original message" in error_message
        assert "Failed after 3/3 attempts" in error_message
        assert "Suggestions:" in error_message


class TestErrorHandlingEdgeCases:
    """Test cases for error handling edge cases."""
    
    @pytest.fixture
    def processor(self):
        """Create a YouTubeProcessor instance for testing."""
        return YouTubeProcessor.from_api_keys(gemini_api_key="test_gemini_key", max_retries=3)
    
    @patch('src.youtube_notion.processors.youtube_processor.time.sleep')
    def test_mixed_error_types_during_retry(self, mock_sleep, processor):
        """Test handling of different error types during retry attempts."""
        mock_func = Mock()
        mock_func.side_effect = [
            APIError("Temporary network error", api_name="Test API"),
            Exception("Unexpected error"),
            "Success"
        ]
        
        result = processor._api_call_with_retry(mock_func)
        
        assert result == "Success"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2
    
    @patch('src.youtube_notion.processors.youtube_processor.time.sleep')
    def test_unexpected_error_conversion_with_retry_info(self, mock_sleep, processor):
        """Test that unexpected errors are converted to APIError with retry info."""
        mock_func = Mock()
        mock_func.side_effect = ValueError("Unexpected value error")
        
        with pytest.raises(APIError) as exc_info:
            processor._api_call_with_retry(mock_func)
        
        error_message = str(exc_info.value)
        assert "Unexpected error during API call" in error_message
        assert "Failed after 3/3 attempts" in error_message
        assert "ValueError" in error_message
    
    def test_is_non_retryable_error_comprehensive(self, processor):
        """Test comprehensive non-retryable error detection."""
        retryable_errors = [
            APIError("Temporary server error", api_name="Test API"),
            APIError("Service unavailable", api_name="Test API"),
            APIError("Internal server error", api_name="Test API"),
        ]
        
        non_retryable_errors = [
            APIError("Invalid API key", api_name="Test API"),
            APIError("Authentication failed", api_name="Test API"),
            APIError("Unauthorized access", api_name="Test API"),
            APIError("Bad request format", api_name="Test API"),
            APIError("Video not found", api_name="Test API"),
            APIError("Method not allowed", api_name="Test API"),
            APIError("Forbidden access", api_name="Test API"),
        ]
        
        for error in retryable_errors:
            assert not processor._is_non_retryable_error(error), f"Error should be retryable: {error}"
        
        for error in non_retryable_errors:
            assert processor._is_non_retryable_error(error), f"Error should not be retryable: {error}"
    
    def test_backoff_calculation_edge_cases(self, processor):
        """Test backoff calculation with edge cases."""
        # Test with attempt 0
        backoff_0 = processor._calculate_backoff_time(0)
        assert 1.0 <= backoff_0 <= 2.0  # 2^0 + jitter
        
        # Test with high attempt number (should be capped)
        backoff_high = processor._calculate_backoff_time(10)
        assert backoff_high <= 60  # Should be capped at 60 seconds
        
        # Test multiple calls return different values due to jitter
        backoff_1a = processor._calculate_backoff_time(1)
        backoff_1b = processor._calculate_backoff_time(1)
        # They might be the same due to timing, but the logic should add jitter
        assert isinstance(backoff_1a, float)
        assert isinstance(backoff_1b, float)