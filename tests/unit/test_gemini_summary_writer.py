"""
Unit tests for GeminiSummaryWriter implementation.

This module tests the GeminiSummaryWriter class with mocked Gemini API responses
and various error scenarios to ensure proper functionality and error handling.
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from src.youtube_notion.writers.gemini_summary_writer import GeminiSummaryWriter
from src.youtube_notion.utils.chat_logger import ChatLogger
from src.youtube_notion.utils.exceptions import (
    SummaryGenerationError,
    ConfigurationError,
    APIError,
    QuotaExceededError
)


class TestGeminiSummaryWriterInitialization:
    """Test GeminiSummaryWriter initialization and configuration."""
    
    def test_init_with_valid_config(self):
        """Test initialization with valid configuration."""
        writer = GeminiSummaryWriter(
            api_key="test_api_key",
            model="gemini-2.0-flash-exp",
            temperature=0.5,
            max_output_tokens=2000,
            max_retries=2,
            timeout_seconds=60
        )
        
        assert writer.api_key == "test_api_key"
        assert writer.model == "gemini-2.0-flash-exp"
        assert writer.temperature == 0.5
        assert writer.max_output_tokens == 2000
        assert writer.max_retries == 2
        assert writer.timeout_seconds == 60
        assert isinstance(writer.chat_logger, ChatLogger)
    
    def test_init_with_custom_chat_logger(self):
        """Test initialization with custom chat logger."""
        custom_logger = Mock(spec=ChatLogger)
        writer = GeminiSummaryWriter(
            api_key="test_api_key",
            chat_logger=custom_logger
        )
        
        assert writer.chat_logger is custom_logger
    
    def test_init_with_defaults(self):
        """Test initialization with default values."""
        writer = GeminiSummaryWriter(api_key="test_api_key")
        
        assert writer.model == "gemini-2.0-flash-exp"
        assert writer.temperature == 0.1
        assert writer.max_output_tokens == 4000
        assert writer.max_retries == 3
        assert writer.timeout_seconds == 120
    
    def test_init_missing_api_key(self):
        """Test initialization fails with missing API key."""
        with pytest.raises(ConfigurationError, match="Gemini API key is required"):
            GeminiSummaryWriter(api_key="")
    
    def test_init_invalid_temperature(self):
        """Test initialization fails with invalid temperature."""
        with pytest.raises(ConfigurationError, match="Temperature must be between 0 and 2"):
            GeminiSummaryWriter(api_key="test_key", temperature=3.0)
        
        with pytest.raises(ConfigurationError, match="Temperature must be between 0 and 2"):
            GeminiSummaryWriter(api_key="test_key", temperature=-0.1)
    
    def test_init_invalid_max_output_tokens(self):
        """Test initialization fails with invalid max output tokens."""
        with pytest.raises(ConfigurationError, match="Max output tokens must be positive"):
            GeminiSummaryWriter(api_key="test_key", max_output_tokens=0)
        
        with pytest.raises(ConfigurationError, match="Max output tokens must be positive"):
            GeminiSummaryWriter(api_key="test_key", max_output_tokens=-100)
    
    def test_init_invalid_max_retries(self):
        """Test initialization fails with invalid max retries."""
        with pytest.raises(ConfigurationError, match="Max retries must be non-negative"):
            GeminiSummaryWriter(api_key="test_key", max_retries=-1)
    
    def test_init_invalid_timeout(self):
        """Test initialization fails with invalid timeout."""
        with pytest.raises(ConfigurationError, match="Timeout seconds must be positive"):
            GeminiSummaryWriter(api_key="test_key", timeout_seconds=0)
        
        with pytest.raises(ConfigurationError, match="Timeout seconds must be positive"):
            GeminiSummaryWriter(api_key="test_key", timeout_seconds=-10)


class TestGeminiSummaryWriterValidation:
    """Test configuration validation methods."""
    
    def test_validate_configuration_success(self):
        """Test successful configuration validation."""
        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client') as mock_client:
            mock_client.return_value = Mock()
            
            writer = GeminiSummaryWriter(api_key="test_api_key")
            result = writer.validate_configuration()
            
            assert result is True
            mock_client.assert_called_once_with(api_key="test_api_key")
    
    def test_validate_configuration_missing_api_key(self):
        """Test validation fails with missing API key."""
        writer = GeminiSummaryWriter(api_key="test_api_key")
        writer.api_key = ""  # Simulate missing key
        
        with pytest.raises(ConfigurationError, match="Gemini API key is not set"):
            writer.validate_configuration()
    
    def test_validate_configuration_invalid_temperature(self):
        """Test validation fails with invalid temperature."""
        writer = GeminiSummaryWriter(api_key="test_api_key")
        writer.temperature = 3.0  # Invalid temperature
        
        with pytest.raises(ConfigurationError, match="Temperature must be between 0 and 2"):
            writer.validate_configuration()
    
    def test_validate_configuration_invalid_client(self):
        """Test validation fails with invalid client initialization."""
        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client') as mock_client:
            mock_client.side_effect = Exception("Invalid API key")
            
            writer = GeminiSummaryWriter(api_key="invalid_key")
            
            with pytest.raises(ConfigurationError, match="Invalid Gemini API key"):
                writer.validate_configuration()


class TestGeminiSummaryWriterSummaryGeneration:
    """Test summary generation functionality."""
    
    @pytest.fixture
    def mock_writer(self):
        """Create a GeminiSummaryWriter with mocked dependencies."""
        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client'):
            writer = GeminiSummaryWriter(api_key="test_api_key")
            writer.chat_logger = Mock(spec=ChatLogger)
            return writer
    
    @pytest.fixture
    def sample_video_metadata(self):
        """Sample video metadata for testing."""
        return {
            'video_id': 'test_video_id',
            'title': 'Test Video Title',
            'channel': 'Test Channel',
            'description': 'Test video description',
            'thumbnail_url': 'https://example.com/thumbnail.jpg'
        }
    
    def test_generate_summary_success(self, mock_writer, sample_video_metadata):
        """Test successful summary generation."""
        expected_summary = "# Test Summary\n\nThis is a test summary with [1:23] timestamp."
        
        with patch.object(mock_writer, '_api_call_with_retry') as mock_retry:
            mock_retry.return_value = expected_summary
            
            result = mock_writer.generate_summary(
                video_url="https://youtube.com/watch?v=test_id",
                video_metadata=sample_video_metadata,
                custom_prompt="Custom test prompt"
            )
            
            assert result == expected_summary
            mock_retry.assert_called_once()
            mock_writer.chat_logger.log_chat.assert_called_once()
    
    def test_generate_summary_with_default_prompt(self, mock_writer, sample_video_metadata):
        """Test summary generation with default prompt."""
        expected_summary = "Default prompt summary"
        
        with patch.object(mock_writer, '_api_call_with_retry') as mock_retry:
            mock_retry.return_value = expected_summary
            
            result = mock_writer.generate_summary(
                video_url="https://youtube.com/watch?v=test_id",
                video_metadata=sample_video_metadata
            )
            
            assert result == expected_summary
            # Verify default prompt was used
            args, kwargs = mock_retry.call_args
            assert args[2] == mock_writer.default_prompt  # prompt is the 3rd argument (index 2)
    
    def test_generate_summary_missing_video_url(self, mock_writer, sample_video_metadata):
        """Test summary generation fails with missing video URL."""
        with pytest.raises(SummaryGenerationError, match="Video URL is required"):
            mock_writer.generate_summary(
                video_url="",
                video_metadata=sample_video_metadata
            )
    
    def test_generate_summary_missing_metadata(self, mock_writer):
        """Test summary generation fails with missing metadata."""
        with pytest.raises(SummaryGenerationError, match="Video metadata is required"):
            mock_writer.generate_summary(
                video_url="https://youtube.com/watch?v=test_id",
                video_metadata=None
            )
    
    def test_generate_summary_logging_failure(self, mock_writer, sample_video_metadata):
        """Test summary generation continues when logging fails."""
        expected_summary = "Test summary"
        mock_writer.chat_logger.log_chat.side_effect = Exception("Logging failed")
        
        with patch.object(mock_writer, '_api_call_with_retry') as mock_retry:
            mock_retry.return_value = expected_summary
            
            # Should not raise exception despite logging failure
            result = mock_writer.generate_summary(
                video_url="https://youtube.com/watch?v=test_id",
                video_metadata=sample_video_metadata
            )
            
            assert result == expected_summary
    
    def test_generate_summary_api_error(self, mock_writer, sample_video_metadata):
        """Test summary generation with API error."""
        with patch.object(mock_writer, '_api_call_with_retry') as mock_retry:
            mock_retry.side_effect = APIError("API call failed", api_name="Gemini API")
            
            with pytest.raises(APIError):
                mock_writer.generate_summary(
                    video_url="https://youtube.com/watch?v=test_id",
                    video_metadata=sample_video_metadata
                )
    
    def test_generate_summary_unexpected_error(self, mock_writer, sample_video_metadata):
        """Test summary generation with unexpected error."""
        with patch.object(mock_writer, '_api_call_with_retry') as mock_retry:
            mock_retry.side_effect = ValueError("Unexpected error")
            
            with pytest.raises(SummaryGenerationError, match="Unexpected error during summary generation"):
                mock_writer.generate_summary(
                    video_url="https://youtube.com/watch?v=test_id",
                    video_metadata=sample_video_metadata
                )


class TestGeminiAPICall:
    """Test Gemini API call functionality."""
    
    @pytest.fixture
    def mock_writer(self):
        """Create a GeminiSummaryWriter for testing."""
        return GeminiSummaryWriter(api_key="test_api_key")
    
    def test_call_gemini_api_success_streaming(self, mock_writer):
        """Test successful Gemini API call with streaming."""
        mock_client = Mock()
        mock_chunk1 = Mock()
        mock_chunk1.text = "First part "
        mock_chunk2 = Mock()
        mock_chunk2.text = "second part."
        
        mock_client.models.generate_content_stream.return_value = [mock_chunk1, mock_chunk2]
        
        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client', return_value=mock_client):
            result = mock_writer._call_gemini_api(
                video_url="https://youtube.com/watch?v=test_id",
                prompt="Test prompt"
            )
            
            assert result == "First part second part."
    
    def test_call_gemini_api_success_non_streaming_fallback(self, mock_writer):
        """Test Gemini API call falls back to non-streaming on streaming failure."""
        mock_client = Mock()
        mock_client.models.generate_content_stream.side_effect = Exception("Streaming failed")
        
        mock_response = Mock()
        mock_response.text = "Non-streaming response"
        mock_client.models.generate_content.return_value = mock_response
        
        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client', return_value=mock_client):
            result = mock_writer._call_gemini_api(
                video_url="https://youtube.com/watch?v=test_id",
                prompt="Test prompt"
            )
            
            assert result == "Non-streaming response"
    
    def test_call_gemini_api_empty_response(self, mock_writer):
        """Test Gemini API call with empty response."""
        mock_client = Mock()
        mock_client.models.generate_content_stream.return_value = []
        
        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client', return_value=mock_client):
            with pytest.raises(APIError, match="Gemini API returned empty response"):
                mock_writer._call_gemini_api(
                    video_url="https://youtube.com/watch?v=test_id",
                    prompt="Test prompt"
                )
    
    def test_call_gemini_api_quota_exceeded(self, mock_writer):
        """Test Gemini API call with quota exceeded error."""
        mock_client = Mock()
        quota_error = Exception("quota exceeded")
        mock_client.models.generate_content_stream.side_effect = quota_error
        mock_client.models.generate_content.side_effect = quota_error  # Also mock non-streaming
        
        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client', return_value=mock_client):
            with pytest.raises(QuotaExceededError):
                mock_writer._call_gemini_api(
                    video_url="https://youtube.com/watch?v=test_id",
                    prompt="Test prompt"
                )
    
    def test_call_gemini_api_authentication_error(self, mock_writer):
        """Test Gemini API call with authentication error."""
        mock_client = Mock()
        auth_error = Exception("unauthorized")
        mock_client.models.generate_content_stream.side_effect = auth_error
        mock_client.models.generate_content.side_effect = auth_error  # Also mock non-streaming
        
        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client', return_value=mock_client):
            with pytest.raises(APIError, match="authentication failed"):
                mock_writer._call_gemini_api(
                    video_url="https://youtube.com/watch?v=test_id",
                    prompt="Test prompt"
                )
    
    def test_call_gemini_api_video_processing_error(self, mock_writer):
        """Test Gemini API call with video processing error."""
        mock_client = Mock()
        video_error = Exception("video unsupported format")
        mock_client.models.generate_content_stream.side_effect = video_error
        mock_client.models.generate_content.side_effect = video_error  # Also mock non-streaming
        
        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client', return_value=mock_client):
            with pytest.raises(APIError, match="could not process the video"):
                mock_writer._call_gemini_api(
                    video_url="https://youtube.com/watch?v=test_id",
                    prompt="Test prompt"
                )

    def test_call_gemini_api_uses_file_data(self, mock_writer):
        """Test that the Gemini API call uses FileData for the video URL."""
        mock_client = Mock()
        mock_client.models.generate_content_stream.return_value = [Mock(text="response")]

        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client', return_value=mock_client) as mock_genai_client:
            mock_writer._call_gemini_api(
                video_url="https://youtube.com/watch?v=test_id",
                prompt="Test prompt"
            )

            mock_genai_client.assert_called_once_with(api_key=mock_writer.api_key)

            call_args, call_kwargs = mock_client.models.generate_content_stream.call_args

            # Check the 'contents' argument
            contents = call_kwargs.get('contents')
            assert contents is not None
            assert len(contents) == 1

            # Check the parts of the content
            parts = contents[0].parts
            assert len(parts) == 2

            # Check the FileData part
            file_part = parts[0]
            assert file_part.file_data is not None
            assert file_part.file_data.file_uri == "https://youtube.com/watch?v=test_id"
            assert file_part.file_data.mime_type == "video/*"

            # Check the text part
            text_part = parts[1]
            assert text_part.text == "Test prompt"


class TestRetryLogic:
    """Test retry logic and error handling."""
    
    @pytest.fixture
    def mock_writer(self):
        """Create a GeminiSummaryWriter with short retry settings."""
        return GeminiSummaryWriter(
            api_key="test_api_key",
            max_retries=2,
            timeout_seconds=30
        )
    
    def test_api_call_with_retry_success_first_attempt(self, mock_writer):
        """Test successful API call on first attempt."""
        mock_func = Mock(return_value="success")
        
        result = mock_writer._api_call_with_retry(mock_func, "arg1", "arg2")
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_api_call_with_retry_success_after_failure(self, mock_writer):
        """Test successful API call after initial failure."""
        mock_func = Mock(side_effect=[
            APIError("Temporary error", api_name="Gemini API"),
            "success"
        ])
        
        with patch('time.sleep'):  # Speed up test
            result = mock_writer._api_call_with_retry(mock_func, "arg1")
            
            assert result == "success"
            assert mock_func.call_count == 2
    
    def test_api_call_with_retry_quota_exceeded_with_delay(self, mock_writer):
        """Test retry with quota exceeded error and retry delay."""
        quota_error = QuotaExceededError(
            "Quota exceeded",
            api_name="Gemini API",
            retry_delay_seconds=10
        )
        mock_func = Mock(side_effect=[quota_error, "success"])
        
        # Mock environment to not be in test mode
        with patch('time.sleep') as mock_sleep, \
             patch.dict('os.environ', {}, clear=True):  # Clear environment to avoid test mode
            result = mock_writer._api_call_with_retry(mock_func, "arg1")
            
            assert result == "success"
            assert mock_func.call_count == 2
            # Should sleep for retry_delay + 15 seconds buffer
            mock_sleep.assert_called_once_with(25)
    
    def test_api_call_with_retry_quota_exceeded_test_mode(self, mock_writer):
        """Test retry with quota exceeded in test mode (capped delay)."""
        quota_error = QuotaExceededError(
            "Quota exceeded",
            api_name="Gemini API",
            retry_delay_seconds=60  # Long delay
        )
        mock_func = Mock(side_effect=[quota_error, "success"])
        
        with patch.dict(os.environ, {'PYTEST_CURRENT_TEST': 'test'}):
            with patch('time.sleep') as mock_sleep:
                result = mock_writer._api_call_with_retry(mock_func, "arg1")
                
                assert result == "success"
                # Should cap delay to 5 seconds in test mode
                mock_sleep.assert_called_once_with(5)
    
    def test_api_call_with_retry_non_retryable_error(self, mock_writer):
        """Test non-retryable error is not retried."""
        auth_error = APIError("Invalid API key", api_name="Gemini API")
        mock_func = Mock(side_effect=auth_error)
        
        with pytest.raises(APIError):
            mock_writer._api_call_with_retry(mock_func, "arg1")
        
        # Should not retry authentication errors
        assert mock_func.call_count == 1
    
    def test_api_call_with_retry_max_retries_exceeded(self, mock_writer):
        """Test max retries exceeded."""
        api_error = APIError("Network error", api_name="Gemini API")
        mock_func = Mock(side_effect=api_error)
        
        with patch('time.sleep'):  # Speed up test
            with pytest.raises(APIError, match="Failed after 2/2 attempts"):
                mock_writer._api_call_with_retry(mock_func, "arg1")
        
        assert mock_func.call_count == 2  # max_retries = 2
    
    def test_is_non_retryable_error(self, mock_writer):
        """Test identification of non-retryable errors."""
        # Authentication errors should not be retried
        auth_error = APIError("Invalid API key", api_name="Gemini API")
        assert mock_writer._is_non_retryable_error(auth_error) is True
        
        # Client errors should not be retried
        client_error = APIError("Bad request", api_name="Gemini API")
        assert mock_writer._is_non_retryable_error(client_error) is True
        
        # Network errors should be retried
        network_error = APIError("Connection timeout", api_name="Gemini API")
        assert mock_writer._is_non_retryable_error(network_error) is False
    
    def test_calculate_backoff_time(self, mock_writer):
        """Test backoff time calculation."""
        # First attempt (attempt=0): 2^0 + jitter = 1 + jitter
        backoff_0 = mock_writer._calculate_backoff_time(0)
        assert 1.0 <= backoff_0 <= 2.0
        
        # Second attempt (attempt=1): 2^1 + jitter = 2 + jitter
        backoff_1 = mock_writer._calculate_backoff_time(1)
        assert 2.0 <= backoff_1 <= 3.0
        
        # Large attempt should be capped at 60 seconds
        backoff_large = mock_writer._calculate_backoff_time(10)
        assert backoff_large <= 60.0


class TestErrorHandling:
    """Test error handling and enhancement."""
    
    @pytest.fixture
    def mock_writer(self):
        """Create a GeminiSummaryWriter for testing."""
        return GeminiSummaryWriter(api_key="test_api_key", max_retries=3)
    
    def test_enhance_error_message_api_error(self, mock_writer):
        """Test error message enhancement for API errors."""
        original_error = APIError("Original message", api_name="Gemini API")
        
        enhanced = mock_writer._enhance_error_message(original_error, 2, 3)
        
        assert isinstance(enhanced, APIError)
        assert "Failed after 2/3 attempts" in str(enhanced)
        assert "Suggestions:" in str(enhanced)
    
    def test_enhance_error_message_quota_error(self, mock_writer):
        """Test error message enhancement for quota errors."""
        original_error = QuotaExceededError(
            "Quota exceeded",
            api_name="Gemini API",
            quota_type="daily",
            retry_delay_seconds=30
        )
        
        enhanced = mock_writer._enhance_error_message(original_error, 1, 3)
        
        assert isinstance(enhanced, QuotaExceededError)
        assert "Failed after 1/3 attempts" in str(enhanced)
        assert "Quota type: daily" in str(enhanced)
        assert "Retry after: 45s" in str(enhanced)  # 30 + 15 buffer
    
    def test_get_error_suggestions(self, mock_writer):
        """Test error suggestion generation."""
        # API key error
        api_key_error = APIError("Invalid API key", api_name="Gemini API")
        suggestion = mock_writer._get_error_suggestions(api_key_error)
        assert "Check your API key" in suggestion
        
        # Quota error
        quota_error = APIError("Quota exceeded", api_name="Gemini API")
        suggestion = mock_writer._get_error_suggestions(quota_error)
        assert "quota limits" in suggestion
        
        # Network error
        network_error = APIError("Connection timeout", api_name="Gemini API")
        suggestion = mock_writer._get_error_suggestions(network_error)
        assert "internet connection" in suggestion
    
    def test_parse_retry_delay_from_error(self, mock_writer):
        """Test parsing retry delay from error messages."""
        # Test with quoted format
        error_with_quotes = "Error: {'retryDelay': '18s'}"
        delay = mock_writer._parse_retry_delay_from_error(error_with_quotes)
        assert delay == 18
        
        # Test with unquoted format
        error_unquoted = "Error: retryDelay: 25s"
        delay = mock_writer._parse_retry_delay_from_error(error_unquoted)
        assert delay == 25
        
        # Test with no retry delay
        error_no_delay = "Generic error message"
        delay = mock_writer._parse_retry_delay_from_error(error_no_delay)
        assert delay is None
        
        # Test with malformed JSON
        error_malformed = "Error: {malformed json}"
        delay = mock_writer._parse_retry_delay_from_error(error_malformed)
        assert delay is None


class TestIntegration:
    """Integration tests for GeminiSummaryWriter."""
    
    def test_full_workflow_success(self):
        """Test complete workflow from initialization to summary generation."""
        mock_client = Mock()
        mock_chunk = Mock()
        mock_chunk.text = "# Video Summary\n\nThis video covers [1:23] important topics."
        mock_client.models.generate_content_stream.return_value = [mock_chunk]
        
        mock_logger = Mock(spec=ChatLogger)
        
        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client', return_value=mock_client):
            writer = GeminiSummaryWriter(
                api_key="test_api_key",
                chat_logger=mock_logger
            )
            
            # Validate configuration
            assert writer.validate_configuration() is True
            
            # Generate summary
            video_metadata = {
                'video_id': 'test_id',
                'title': 'Test Video',
                'channel': 'Test Channel'
            }
            
            result = writer.generate_summary(
                video_url="https://youtube.com/watch?v=test_id",
                video_metadata=video_metadata,
                custom_prompt="Summarize this video"
            )
            
            assert result == "# Video Summary\n\nThis video covers [1:23] important topics."
            mock_logger.log_chat.assert_called_once()
    
    def test_configuration_validation_integration(self):
        """Test configuration validation with various scenarios."""
        # Valid configuration
        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client'):
            writer = GeminiSummaryWriter(api_key="valid_key")
            assert writer.validate_configuration() is True
        
        # Invalid temperature
        writer = GeminiSummaryWriter(api_key="valid_key", temperature=0.5)
        writer.temperature = 3.0  # Set invalid after init
        with pytest.raises(ConfigurationError):
            writer.validate_configuration()
        
        # Invalid client initialization
        with patch('src.youtube_notion.writers.gemini_summary_writer.genai.Client', side_effect=Exception("Client error")):
            writer = GeminiSummaryWriter(api_key="invalid_key")
            with pytest.raises(ConfigurationError):
                writer.validate_configuration()