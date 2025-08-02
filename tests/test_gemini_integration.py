"""
Unit tests for Google Gemini integration in YouTube processor.

This module tests the Gemini API integration functionality including:
- Summary generation with streaming responses
- Error handling for various API failures
- Retry logic with exponential backoff
- Prompt configuration and customization
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time
from google.genai import types

from youtube_notion.processors.youtube_processor import YouTubeProcessor, DEFAULT_SUMMARY_PROMPT
from youtube_notion.processors.exceptions import APIError, QuotaExceededError


class TestGeminiIntegration:
    """Test cases for Gemini API integration."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = YouTubeProcessor(
            gemini_api_key="test_gemini_key",
            youtube_api_key="test_youtube_key"
        )
        self.test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.test_prompt = "Summarize this video with timestamps."
    
    @patch('youtube_notion.processors.youtube_processor.genai.Client')
    def test_generate_summary_success_streaming(self, mock_client_class):
        """Test successful summary generation with streaming response."""
        # Mock the client and streaming response
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock streaming chunks
        mock_chunks = [
            Mock(text="# Video Summary\n\n"),
            Mock(text="This video covers important topics:\n\n"),
            Mock(text="- [2:30] First key point\n"),
            Mock(text="- [5:15] Second key point\n"),
            Mock(text="- [8:45-9:30] Detailed explanation")
        ]
        
        mock_client.models.generate_content_stream.return_value = iter(mock_chunks)
        
        # Call the method
        result = self.processor._generate_summary(self.test_video_url, self.test_prompt)
        
        # Verify the result
        expected_summary = (
            "# Video Summary\n\n"
            "This video covers important topics:\n\n"
            "- [2:30] First key point\n"
            "- [5:15] Second key point\n"
            "- [8:45-9:30] Detailed explanation"
        )
        assert result == expected_summary
        
        # Verify API call was made correctly
        mock_client_class.assert_called_once_with(api_key="test_gemini_key")
        mock_client.models.generate_content_stream.assert_called_once()
        
        # Verify the call arguments
        call_args = mock_client.models.generate_content_stream.call_args
        assert call_args[1]['model'] == "gemini-2.0-flash-exp"
        assert len(call_args[1]['contents']) == 1
        
        content = call_args[1]['contents'][0]
        assert content.role == "user"
        assert len(content.parts) == 2
        
        # Check file data part
        file_part = content.parts[0]
        assert file_part.file_data.file_uri == self.test_video_url
        assert file_part.file_data.mime_type == "video/*"
        
        # Check text part
        text_part = content.parts[1]
        assert text_part.text == self.test_prompt
    
    @patch('youtube_notion.processors.youtube_processor.genai.Client')
    def test_generate_summary_fallback_to_non_streaming(self, mock_client_class):
        """Test fallback to non-streaming when streaming fails."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock streaming to raise an exception
        mock_client.models.generate_content_stream.side_effect = Exception("Streaming failed")
        
        # Mock non-streaming response
        mock_response = Mock()
        mock_response.text = "# Fallback Summary\n\nThis is a fallback response."
        mock_client.models.generate_content.return_value = mock_response
        
        # Call the method
        result = self.processor._generate_summary(self.test_video_url, self.test_prompt)
        
        # Verify the result
        assert result == "# Fallback Summary\n\nThis is a fallback response."
        
        # Verify both streaming and non-streaming were called
        mock_client.models.generate_content_stream.assert_called_once()
        mock_client.models.generate_content.assert_called_once()
    
    @patch('youtube_notion.processors.youtube_processor.genai.Client')
    def test_generate_summary_uses_default_prompt(self, mock_client_class):
        """Test that default prompt is used when none provided."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_chunks = [Mock(text="Summary with default prompt")]
        mock_client.models.generate_content_stream.return_value = iter(mock_chunks)
        
        # Call without prompt
        result = self.processor._generate_summary(self.test_video_url)
        
        # Verify default prompt was used
        call_args = mock_client.models.generate_content_stream.call_args
        text_part = call_args[1]['contents'][0].parts[1]
        assert text_part.text == DEFAULT_SUMMARY_PROMPT
    
    @patch('youtube_notion.processors.youtube_processor.genai.Client')
    def test_generate_summary_custom_prompt(self, mock_client_class):
        """Test that custom prompt is used correctly."""
        custom_prompt = "Custom prompt for testing"
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_chunks = [Mock(text="Summary with custom prompt")]
        mock_client.models.generate_content_stream.return_value = iter(mock_chunks)
        
        # Call with custom prompt
        result = self.processor._generate_summary(self.test_video_url, custom_prompt)
        
        # Verify custom prompt was used
        call_args = mock_client.models.generate_content_stream.call_args
        text_part = call_args[1]['contents'][0].parts[1]
        assert text_part.text == custom_prompt
    
    @patch('youtube_notion.processors.youtube_processor.genai.Client')
    def test_generate_summary_empty_response_error(self, mock_client_class):
        """Test error handling for empty API response."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock empty streaming response
        mock_chunks = [Mock(text=""), Mock(text="   ")]  # Empty and whitespace only
        mock_client.models.generate_content_stream.return_value = iter(mock_chunks)
        
        # Should raise APIError for empty response
        with pytest.raises(APIError) as exc_info:
            self.processor._generate_summary(self.test_video_url, self.test_prompt)
        
        assert "empty response" in str(exc_info.value)
        assert exc_info.value.api_name == "Gemini API"
    
    @patch('youtube_notion.processors.youtube_processor.genai.Client')
    def test_generate_summary_quota_exceeded_error(self, mock_client_class):
        """Test handling of quota exceeded errors."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock quota exceeded error for both streaming and non-streaming
        quota_error = Exception("Quota exceeded for requests")
        mock_client.models.generate_content_stream.side_effect = quota_error
        mock_client.models.generate_content.side_effect = quota_error
        
        with pytest.raises(QuotaExceededError) as exc_info:
            self.processor._generate_summary(self.test_video_url, self.test_prompt)
        
        assert "quota" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Gemini API"
        assert exc_info.value.quota_type == "quota"
    
    @patch('youtube_notion.processors.youtube_processor.genai.Client')
    def test_generate_summary_rate_limit_error(self, mock_client_class):
        """Test handling of rate limit errors."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock rate limit error for both streaming and non-streaming
        rate_limit_error = Exception("Rate limit exceeded")
        mock_client.models.generate_content_stream.side_effect = rate_limit_error
        mock_client.models.generate_content.side_effect = rate_limit_error
        
        with pytest.raises(QuotaExceededError) as exc_info:
            self.processor._generate_summary(self.test_video_url, self.test_prompt)
        
        assert "rate limit" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Gemini API"
        assert exc_info.value.quota_type == "rate_limit"
    
    @patch('youtube_notion.processors.youtube_processor.genai.Client')
    def test_generate_summary_authentication_error(self, mock_client_class):
        """Test handling of authentication errors."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock authentication error for both streaming and non-streaming
        auth_error = Exception("Invalid API key")
        mock_client.models.generate_content_stream.side_effect = auth_error
        mock_client.models.generate_content.side_effect = auth_error
        
        with pytest.raises(APIError) as exc_info:
            self.processor._generate_summary(self.test_video_url, self.test_prompt)
        
        assert "authentication failed" in str(exc_info.value).lower()
        assert "api key" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Gemini API"
    
    @patch('youtube_notion.processors.youtube_processor.genai.Client')
    def test_generate_summary_video_processing_error(self, mock_client_class):
        """Test handling of video processing errors."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock video processing error for both streaming and non-streaming
        video_error = Exception("Unsupported video format")
        mock_client.models.generate_content_stream.side_effect = video_error
        mock_client.models.generate_content.side_effect = video_error
        
        with pytest.raises(APIError) as exc_info:
            self.processor._generate_summary(self.test_video_url, self.test_prompt)
        
        assert "could not process the video" in str(exc_info.value).lower()
        assert exc_info.value.api_name == "Gemini API"
        assert self.test_video_url in exc_info.value.details
    
    @patch('youtube_notion.processors.youtube_processor.genai.Client')
    def test_generate_summary_generic_api_error(self, mock_client_class):
        """Test handling of generic API errors."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        # Mock generic error for both streaming and non-streaming
        generic_error = Exception("Unknown API error")
        mock_client.models.generate_content_stream.side_effect = generic_error
        mock_client.models.generate_content.side_effect = generic_error
        
        with pytest.raises(APIError) as exc_info:
            self.processor._generate_summary(self.test_video_url, self.test_prompt)
        
        assert "Gemini API call failed" in str(exc_info.value)
        assert exc_info.value.api_name == "Gemini API"


class TestRetryLogic:
    """Test cases for API retry logic."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = YouTubeProcessor(
            gemini_api_key="test_gemini_key",
            max_retries=3
        )
    
    @patch('youtube_notion.processors.youtube_processor.time.sleep')
    def test_api_call_with_retry_success_after_failure(self, mock_sleep):
        """Test successful retry after initial failure."""
        mock_func = Mock()
        mock_func.side_effect = [
            APIError("Temporary error", api_name="Test API"),
            "Success on second try"
        ]
        
        result = self.processor._api_call_with_retry(mock_func, "arg1", kwarg1="value1")
        
        assert result == "Success on second try"
        assert mock_func.call_count == 2
        mock_sleep.assert_called_once()  # Should sleep once between retries
    
    @patch('youtube_notion.processors.youtube_processor.time.sleep')
    def test_api_call_with_retry_quota_error_no_retry(self, mock_sleep):
        """Test that quota errors are not retried."""
        mock_func = Mock()
        mock_func.side_effect = QuotaExceededError("Quota exceeded", api_name="Test API")
        
        with pytest.raises(QuotaExceededError):
            self.processor._api_call_with_retry(mock_func)
        
        assert mock_func.call_count == 1  # Should not retry
        mock_sleep.assert_not_called()
    
    @patch('youtube_notion.processors.youtube_processor.time.sleep')
    def test_api_call_with_retry_authentication_error_no_retry(self, mock_sleep):
        """Test that authentication errors are not retried."""
        mock_func = Mock()
        mock_func.side_effect = APIError("Invalid API key", api_name="Test API")
        
        with pytest.raises(APIError) as exc_info:
            self.processor._api_call_with_retry(mock_func)
        
        assert "api key" in str(exc_info.value).lower()
        assert mock_func.call_count == 1  # Should not retry
        mock_sleep.assert_not_called()
    
    @patch('youtube_notion.processors.youtube_processor.time.sleep')
    def test_api_call_with_retry_max_retries_exceeded(self, mock_sleep):
        """Test behavior when max retries are exceeded."""
        mock_func = Mock()
        mock_func.side_effect = APIError("Persistent error", api_name="Test API")
        
        with pytest.raises(APIError) as exc_info:
            self.processor._api_call_with_retry(mock_func)
        
        assert "Persistent error" in str(exc_info.value)
        assert mock_func.call_count == 3  # Should try max_retries times
        assert mock_sleep.call_count == 2  # Should sleep between retries
    
    @patch('youtube_notion.processors.youtube_processor.time.sleep')
    def test_api_call_with_retry_exponential_backoff(self, mock_sleep):
        """Test exponential backoff timing."""
        mock_func = Mock()
        mock_func.side_effect = [
            APIError("Error 1", api_name="Test API"),
            APIError("Error 2", api_name="Test API"),
            APIError("Error 3", api_name="Test API")
        ]
        
        with pytest.raises(APIError):
            self.processor._api_call_with_retry(mock_func)
        
        # Verify exponential backoff (with jitter, so we check the base values)
        sleep_calls = mock_sleep.call_args_list
        assert len(sleep_calls) == 2
        
        # First backoff should be around 1 second (2^0 + jitter)
        first_sleep = sleep_calls[0][0][0]
        assert 1 <= first_sleep < 2
        
        # Second backoff should be around 2 seconds (2^1 + jitter)
        second_sleep = sleep_calls[1][0][0]
        assert 2 <= second_sleep < 3
    
    @patch('youtube_notion.processors.youtube_processor.time.sleep')
    def test_api_call_with_retry_unexpected_error_conversion(self, mock_sleep):
        """Test conversion of unexpected errors to APIError."""
        mock_func = Mock()
        mock_func.side_effect = ValueError("Unexpected error")
        
        with pytest.raises(APIError) as exc_info:
            self.processor._api_call_with_retry(mock_func)
        
        assert "Unexpected error during API call" in str(exc_info.value)
        assert exc_info.value.api_name == "Unknown"


class TestProcessorConfiguration:
    """Test cases for processor configuration."""
    
    def test_processor_initialization_with_defaults(self):
        """Test processor initialization with default configuration."""
        processor = YouTubeProcessor(gemini_api_key="test_key")
        
        assert processor.gemini_api_key == "test_key"
        assert processor.youtube_api_key is None
        assert processor.default_prompt == DEFAULT_SUMMARY_PROMPT
        assert processor.max_retries == 3
        assert processor.timeout_seconds == 120
    
    def test_processor_initialization_with_custom_config(self):
        """Test processor initialization with custom configuration."""
        custom_prompt = "Custom prompt for testing"
        
        processor = YouTubeProcessor(
            gemini_api_key="test_key",
            youtube_api_key="youtube_key",
            default_prompt=custom_prompt,
            max_retries=5,
            timeout_seconds=180
        )
        
        assert processor.gemini_api_key == "test_key"
        assert processor.youtube_api_key == "youtube_key"
        assert processor.default_prompt == custom_prompt
        assert processor.max_retries == 5
        assert processor.timeout_seconds == 180
    
    def test_processor_initialization_missing_gemini_key(self):
        """Test that missing Gemini API key raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            YouTubeProcessor(gemini_api_key="")
        
        assert "Gemini API key is required" in str(exc_info.value)
        
        with pytest.raises(ValueError) as exc_info:
            YouTubeProcessor(gemini_api_key=None)
        
        assert "Gemini API key is required" in str(exc_info.value)


class TestGenerateContentConfig:
    """Test cases for Gemini API configuration."""
    
    @patch('youtube_notion.processors.youtube_processor.genai.Client')
    def test_generate_content_config_parameters(self, mock_client_class):
        """Test that correct configuration is passed to Gemini API."""
        processor = YouTubeProcessor(gemini_api_key="test_key")
        
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        
        mock_chunks = [Mock(text="Test response")]
        mock_client.models.generate_content_stream.return_value = iter(mock_chunks)
        
        # Call the method
        processor._generate_summary("https://www.youtube.com/watch?v=test", "Test prompt")
        
        # Verify configuration parameters
        call_args = mock_client.models.generate_content_stream.call_args
        config = call_args[1]['config']
        
        assert config.temperature == 0.1
        assert config.max_output_tokens == 4000
        assert config.response_mime_type == "text/plain"