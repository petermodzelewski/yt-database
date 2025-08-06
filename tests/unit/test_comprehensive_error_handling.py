"""
Comprehensive error handling tests for the new architecture.

This module tests error handling across all components and ensures
proper error propagation, user-friendly messages, and graceful degradation.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.youtube_notion.utils.exceptions import (
    VideoProcessingError,
    ConfigurationError,
    MetadataExtractionError,
    SummaryGenerationError,
    StorageError,
    InvalidURLError,
    APIError,
    VideoUnavailableError,
    QuotaExceededError
)
from src.youtube_notion.processors.video_processor import VideoProcessor
from src.youtube_notion.extractors.video_metadata_extractor import VideoMetadataExtractor
from src.youtube_notion.writers.gemini_summary_writer import GeminiSummaryWriter
from src.youtube_notion.storage.notion_storage import NotionStorage
from src.youtube_notion.config.factory import ComponentFactory
from src.youtube_notion.config.settings import ApplicationConfig, YouTubeProcessorConfig, NotionConfig
from tests.fixtures.mock_implementations import (
    MockMetadataExtractor, 
    MockSummaryWriter, 
    MockStorage,
    create_successful_mocks,
    create_failing_mocks
)


class TestVideoProcessorErrorHandling:
    """Test error handling in the VideoProcessor orchestrator."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor, self.writer, self.storage = create_successful_mocks()
        self.processor = VideoProcessor(self.extractor, self.writer, self.storage)
    
    def test_initialization_with_none_components(self):
        """Test that VideoProcessor raises ConfigurationError for None components."""
        with pytest.raises(ConfigurationError, match="VideoMetadataExtractor is required"):
            VideoProcessor(None, self.writer, self.storage)
        
        with pytest.raises(ConfigurationError, match="SummaryWriter is required"):
            VideoProcessor(self.extractor, None, self.storage)
        
        with pytest.raises(ConfigurationError, match="Storage is required"):
            VideoProcessor(self.extractor, self.writer, None)
    
    def test_process_video_invalid_url_type(self):
        """Test processing with invalid URL types."""
        invalid_urls = [None, 123, [], {}, True]
        
        for invalid_url in invalid_urls:
            with pytest.raises(VideoProcessingError) as exc_info:
                self.processor.process_video(invalid_url)
            
            assert "Video URL must be a non-empty string" in str(exc_info.value)
            assert f"Received: {type(invalid_url).__name__}" in str(exc_info.value.details)
    
    def test_process_video_metadata_extraction_failure(self):
        """Test processing when metadata extraction fails."""
        # Configure extractor to fail
        self.extractor.set_failure_for_url("https://youtu.be/test123")
        
        with pytest.raises(MetadataExtractionError) as exc_info:
            self.processor.process_video("https://youtu.be/test123")
        
        assert "Mock metadata extraction failed" in str(exc_info.value)
        assert "Configured to fail in mock implementation" in str(exc_info.value.details)
    
    def test_process_video_summary_generation_failure(self):
        """Test processing when summary generation fails."""
        # Configure writer to fail
        self.writer.set_failure_for_url("https://youtu.be/test123")
        
        with pytest.raises(SummaryGenerationError) as exc_info:
            self.processor.process_video("https://youtu.be/test123")
        
        assert "Mock summary generation failed" in str(exc_info.value)
        assert "Configured to fail in mock implementation" in str(exc_info.value.details)
    
    def test_process_video_storage_failure(self):
        """Test processing when storage fails."""
        # Configure storage to fail on the video title
        test_url = "https://youtu.be/test123"
        self.storage.set_failure_for_title("Mock Video for test123")
        
        with pytest.raises(StorageError) as exc_info:
            self.processor.process_video(test_url)
        
        assert "Mock storage failed for video" in str(exc_info.value)
        assert "Configured to fail in mock implementation" in str(exc_info.value.details)
    
    def test_process_video_unexpected_error_wrapping(self):
        """Test that unexpected errors are wrapped in VideoProcessingError."""
        # Mock the extractor to raise an unexpected error
        self.extractor.extract_metadata = Mock(side_effect=ValueError("Unexpected error"))
        
        with pytest.raises(VideoProcessingError) as exc_info:
            self.processor.process_video("https://youtu.be/test123")
        
        assert "Unexpected error during video processing" in str(exc_info.value)
        assert "ValueError" in str(exc_info.value.details)
    
    def test_validate_configuration_all_valid(self):
        """Test configuration validation when all components are valid."""
        result = self.processor.validate_configuration()
        assert result is True
    
    def test_validate_configuration_extractor_invalid(self):
        """Test configuration validation when extractor is invalid."""
        self.extractor.configuration_valid = False
        
        with pytest.raises(ConfigurationError) as exc_info:
            self.processor.validate_configuration()
        
        assert "Component configuration validation failed" in str(exc_info.value)
        assert "VideoMetadataExtractor" in str(exc_info.value.details)
    
    def test_validate_configuration_writer_invalid(self):
        """Test configuration validation when writer is invalid."""
        self.writer.configuration_valid = False
        
        with pytest.raises(ConfigurationError) as exc_info:
            self.processor.validate_configuration()
        
        assert "Component configuration validation failed" in str(exc_info.value)
        assert "SummaryWriter" in str(exc_info.value.details)
    
    def test_validate_configuration_storage_invalid(self):
        """Test configuration validation when storage is invalid."""
        self.storage.configuration_valid = False
        
        with pytest.raises(ConfigurationError) as exc_info:
            self.processor.validate_configuration()
        
        assert "Component configuration validation failed" in str(exc_info.value)
        assert "Storage" in str(exc_info.value.details)
    
    def test_validate_configuration_multiple_invalid(self):
        """Test configuration validation when multiple components are invalid."""
        self.extractor.configuration_valid = False
        self.writer.configuration_valid = False
        
        with pytest.raises(ConfigurationError) as exc_info:
            self.processor.validate_configuration()
        
        error_details = str(exc_info.value.details)
        assert "VideoMetadataExtractor" in error_details
        assert "SummaryWriter" in error_details
    
    def test_get_component_info_with_invalid_configuration(self):
        """Test component info when configuration is invalid."""
        self.writer.configuration_valid = False
        
        info = self.processor.get_component_info()
        
        assert info["metadata_extractor"] == "MockMetadataExtractor"
        assert info["summary_writer"] == "MockSummaryWriter"
        assert info["storage"] == "MockStorage"
        assert "invalid" in info["configuration_status"]
        assert "Component configuration validation failed" in info["configuration_status"]


class TestComponentFactoryErrorHandling:
    """Test error handling in the ComponentFactory."""
    
    def test_factory_initialization_invalid_config(self):
        """Test factory initialization with invalid configuration."""
        with pytest.raises(ConfigurationError, match="Application configuration is required"):
            ComponentFactory(None)
        
        with pytest.raises(ConfigurationError, match="Invalid application configuration type"):
            ComponentFactory("invalid_config")
    
    def test_factory_validation_without_proper_config(self):
        """Test that factory requires proper configuration objects."""
        # Test with minimal valid configuration structure
        from src.youtube_notion.config.settings import ApplicationConfig, NotionConfig
        
        # Create a minimal valid config
        notion_config = NotionConfig(
            notion_token="test_token",
            database_name="Test DB",
            parent_page_name="Test Page"
        )
        
        config = ApplicationConfig(
            notion=notion_config,
            youtube_processor=None,  # This should cause issues when creating summary writer
            debug=False,
            verbose=False
        )
        
        factory = ComponentFactory(config)
        
        # Should fail when trying to create summary writer without YouTube config
        with pytest.raises(ConfigurationError, match="YouTube processor configuration is required"):
            factory.create_summary_writer()


class TestMetadataExtractorErrorHandling:
    """Test error handling in VideoMetadataExtractor."""
    
    def test_initialization_invalid_timeout(self):
        """Test initialization with invalid timeout."""
        with pytest.raises(ConfigurationError, match="Timeout seconds must be positive"):
            VideoMetadataExtractor(timeout_seconds=0)
        
        with pytest.raises(ConfigurationError, match="Timeout seconds must be positive"):
            VideoMetadataExtractor(timeout_seconds=-5)
    
    def test_validate_configuration_invalid_timeout(self):
        """Test configuration validation with invalid timeout."""
        extractor = VideoMetadataExtractor(youtube_api_key="test_key", timeout_seconds=10)
        extractor.timeout_seconds = 0  # Make it invalid after initialization
        
        with pytest.raises(ConfigurationError, match="Timeout seconds must be positive"):
            extractor.validate_configuration()
    
    def test_validate_configuration_empty_api_key(self):
        """Test configuration validation with empty API key."""
        extractor = VideoMetadataExtractor(youtube_api_key="   ", timeout_seconds=10)
        
        with pytest.raises(ConfigurationError, match="YouTube API key cannot be empty"):
            extractor.validate_configuration()
    
    def test_extract_video_id_invalid_types(self):
        """Test video ID extraction with invalid input types."""
        extractor = VideoMetadataExtractor()
        
        invalid_inputs = [None, 123, [], {}, True]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(InvalidURLError) as exc_info:
                extractor.extract_video_id(invalid_input)
            
            assert "URL must be a non-empty string" in str(exc_info.value)
            assert f"Received: {type(invalid_input).__name__}" in str(exc_info.value.details)
    
    def test_extract_video_id_empty_string(self):
        """Test video ID extraction with empty string."""
        extractor = VideoMetadataExtractor()
        
        with pytest.raises(InvalidURLError) as exc_info:
            extractor.extract_video_id("")
        
        assert "URL must be a non-empty string" in str(exc_info.value)
        assert "Received: str" in str(exc_info.value.details)
    
    def test_extract_video_id_invalid_domain(self):
        """Test video ID extraction with invalid domain."""
        extractor = VideoMetadataExtractor()
        
        with pytest.raises(InvalidURLError) as exc_info:
            extractor.extract_video_id("https://vimeo.com/123456789")
        
        assert "URL is not from a supported YouTube domain" in str(exc_info.value)
        assert "Domain: vimeo.com" in str(exc_info.value.details)
    
    def test_extract_video_id_malformed_url(self):
        """Test video ID extraction with malformed URL."""
        extractor = VideoMetadataExtractor()
        
        with pytest.raises(InvalidURLError) as exc_info:
            extractor.extract_video_id("https://youtube.com/watch?v=")
        
        assert "Could not extract video ID from URL" in str(exc_info.value)
    
    def test_extract_video_id_invalid_video_id_format(self):
        """Test video ID extraction with invalid video ID format."""
        extractor = VideoMetadataExtractor()
        
        with pytest.raises(InvalidURLError) as exc_info:
            extractor.extract_video_id("https://youtube.com/watch?v=short")
        
        assert "Extracted video ID has invalid format" in str(exc_info.value)
        assert "Video ID: short" in str(exc_info.value.details)
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_web_scraping_timeout_error(self, mock_get):
        """Test web scraping with timeout error."""
        import requests
        
        extractor = VideoMetadataExtractor(timeout_seconds=5)
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        with pytest.raises(APIError) as exc_info:
            extractor._get_metadata_via_scraping("dQw4w9WgXcQ")
        
        assert "Request timed out while scraping YouTube page" in str(exc_info.value)
        assert "Timeout: 5s" in str(exc_info.value.details)
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_web_scraping_connection_error(self, mock_get):
        """Test web scraping with connection error."""
        import requests
        
        extractor = VideoMetadataExtractor()
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(APIError) as exc_info:
            extractor._get_metadata_via_scraping("dQw4w9WgXcQ")
        
        assert "Connection error while scraping YouTube page" in str(exc_info.value)
        assert "Check your internet connection" in str(exc_info.value.details)
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_web_scraping_http_error(self, mock_get):
        """Test web scraping with HTTP error."""
        import requests
        
        extractor = VideoMetadataExtractor()
        
        # Create a mock response with status code
        mock_response = Mock()
        mock_response.status_code = 429
        
        http_error = requests.exceptions.HTTPError("429 Too Many Requests")
        http_error.response = mock_response
        mock_get.side_effect = http_error
        
        with pytest.raises(APIError) as exc_info:
            extractor._get_metadata_via_scraping("dQw4w9WgXcQ")
        
        assert "HTTP error 429 while scraping YouTube page" in str(exc_info.value)
        assert "YouTube is rate limiting requests" in str(exc_info.value.details)


class TestGeminiSummaryWriterErrorHandling:
    """Test error handling in GeminiSummaryWriter."""
    
    def test_initialization_invalid_api_key(self):
        """Test initialization with invalid API key."""
        with pytest.raises(ConfigurationError, match="Gemini API key is required"):
            GeminiSummaryWriter("")
        
        with pytest.raises(ConfigurationError, match="Gemini API key is required"):
            GeminiSummaryWriter(None)
    
    def test_initialization_invalid_temperature(self):
        """Test initialization with invalid temperature."""
        with pytest.raises(ConfigurationError, match="Temperature must be between 0 and 2"):
            GeminiSummaryWriter("test_key", temperature=-0.1)
        
        with pytest.raises(ConfigurationError, match="Temperature must be between 0 and 2"):
            GeminiSummaryWriter("test_key", temperature=2.1)
    
    def test_initialization_invalid_max_output_tokens(self):
        """Test initialization with invalid max output tokens."""
        with pytest.raises(ConfigurationError, match="Max output tokens must be positive"):
            GeminiSummaryWriter("test_key", max_output_tokens=0)
        
        with pytest.raises(ConfigurationError, match="Max output tokens must be positive"):
            GeminiSummaryWriter("test_key", max_output_tokens=-100)
    
    def test_initialization_invalid_max_retries(self):
        """Test initialization with invalid max retries."""
        with pytest.raises(ConfigurationError, match="Max retries must be non-negative"):
            GeminiSummaryWriter("test_key", max_retries=-1)
    
    def test_initialization_invalid_timeout(self):
        """Test initialization with invalid timeout."""
        with pytest.raises(ConfigurationError, match="Timeout seconds must be positive"):
            GeminiSummaryWriter("test_key", timeout_seconds=0)
        
        with pytest.raises(ConfigurationError, match="Timeout seconds must be positive"):
            GeminiSummaryWriter("test_key", timeout_seconds=-30)
    
    def test_generate_summary_empty_url(self):
        """Test summary generation with empty URL."""
        writer = GeminiSummaryWriter("test_key")
        
        with pytest.raises(SummaryGenerationError, match="Video URL is required"):
            writer.generate_summary("", {"title": "Test"})
        
        with pytest.raises(SummaryGenerationError, match="Video URL is required"):
            writer.generate_summary(None, {"title": "Test"})
    
    def test_generate_summary_empty_metadata(self):
        """Test summary generation with empty metadata."""
        writer = GeminiSummaryWriter("test_key")
        
        with pytest.raises(SummaryGenerationError, match="Video metadata is required"):
            writer.generate_summary("https://youtu.be/test", {})
        
        with pytest.raises(SummaryGenerationError, match="Video metadata is required"):
            writer.generate_summary("https://youtu.be/test", None)
    
    def test_validate_configuration_invalid_temperature(self):
        """Test configuration validation with invalid temperature."""
        writer = GeminiSummaryWriter("test_key", temperature=0.5)
        writer.temperature = -0.1  # Make it invalid after initialization
        
        with pytest.raises(ConfigurationError, match="Temperature must be between 0 and 2"):
            writer.validate_configuration()
    
    def test_validate_configuration_invalid_max_output_tokens(self):
        """Test configuration validation with invalid max output tokens."""
        writer = GeminiSummaryWriter("test_key")
        writer.max_output_tokens = 0  # Make it invalid after initialization
        
        with pytest.raises(ConfigurationError, match="Max output tokens must be positive"):
            writer.validate_configuration()


class TestNotionStorageErrorHandling:
    """Test error handling in NotionStorage."""
    
    def test_initialization_invalid_token(self):
        """Test initialization with invalid token."""
        with pytest.raises(ConfigurationError, match="Notion token is required"):
            NotionStorage("", "DB Name", "Page Name")
        
        with pytest.raises(ConfigurationError, match="Notion token is required"):
            NotionStorage("   ", "DB Name", "Page Name")
    
    def test_initialization_invalid_database_name(self):
        """Test initialization with invalid database name."""
        with pytest.raises(ConfigurationError, match="Database name is required"):
            NotionStorage("token", "", "Page Name")
        
        with pytest.raises(ConfigurationError, match="Database name is required"):
            NotionStorage("token", "   ", "Page Name")
    
    def test_initialization_invalid_parent_page_name(self):
        """Test initialization with invalid parent page name."""
        # Empty parent page name is now allowed (optional)
        storage = NotionStorage("token", "DB Name", "")
        assert storage.parent_page_name == ""
        
        # But whitespace-only parent page name should still be invalid
        with pytest.raises(ConfigurationError, match="Parent page name cannot be whitespace-only"):
            NotionStorage("token", "DB Name", "   ")
    
    def test_initialization_invalid_max_retries(self):
        """Test initialization with invalid max retries."""
        with pytest.raises(ConfigurationError, match="Max retries must be non-negative"):
            NotionStorage("token", "DB Name", "Page Name", max_retries=-1)
    
    def test_initialization_invalid_timeout(self):
        """Test initialization with invalid timeout."""
        with pytest.raises(ConfigurationError, match="Timeout seconds must be positive"):
            NotionStorage("token", "DB Name", "Page Name", timeout_seconds=0)
        
        with pytest.raises(ConfigurationError, match="Timeout seconds must be positive"):
            NotionStorage("token", "DB Name", "Page Name", timeout_seconds=-30)
    
    def test_store_video_summary_missing_required_fields(self):
        """Test storing video summary with missing required fields."""
        storage = NotionStorage("token", "DB Name", "Page Name")
        
        # Mock the find_target_location to return a valid ID
        storage.find_target_location = Mock(return_value="mock-db-id")
        
        required_fields = ['Title', 'Channel', 'Video URL', 'Summary']
        
        for field in required_fields:
            incomplete_data = {f: f"test_{f}" for f in required_fields if f != field}
            
            with pytest.raises(StorageError, match=f"Missing required field: {field}"):
                storage.store_video_summary(incomplete_data)
    
    def test_validate_configuration_missing_token(self):
        """Test configuration validation with missing token."""
        storage = NotionStorage("token", "DB Name", "Page Name")
        storage.notion_token = ""  # Make it invalid after initialization
        
        with pytest.raises(ConfigurationError, match="Notion token is required"):
            storage.validate_configuration()
    
    def test_validate_configuration_missing_database_name(self):
        """Test configuration validation with missing database name."""
        storage = NotionStorage("token", "DB Name", "Page Name")
        storage.database_name = ""  # Make it invalid after initialization
        
        with pytest.raises(ConfigurationError, match="Database name is required"):
            storage.validate_configuration()
    
    def test_validate_configuration_empty_parent_page_name_allowed(self):
        """Test configuration validation allows empty parent page name."""
        storage = NotionStorage("token", "DB Name", "Page Name")
        storage.parent_page_name = ""  # Empty parent page name is now allowed
        
        # This should not raise an error for empty parent page name
        # (though it may raise other errors due to invalid token, which we'll mock)
        with patch('src.youtube_notion.storage.notion_storage.Client') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            mock_client.search.return_value = {"results": []}
            
            # Should not raise ConfigurationError for empty parent page name
            result = storage.validate_configuration()
            assert result is True


class TestErrorMessageEnhancements:
    """Test error message enhancements and user-friendly messages."""
    
    def test_configuration_error_with_details(self):
        """Test ConfigurationError with details."""
        error = ConfigurationError(
            "Configuration validation failed",
            details="Missing API key and invalid timeout"
        )
        
        error_str = str(error)
        assert "Configuration validation failed" in error_str
        assert "Missing API key and invalid timeout" in error_str
    
    def test_api_error_with_context(self):
        """Test APIError with additional context."""
        error = APIError(
            "API call failed",
            api_name="Test API",
            status_code=429,
            details="Rate limit exceeded"
        )
        
        error_str = str(error)
        assert "API call failed" in error_str
        assert "API: Test API" in error_str
        assert "Status: 429" in error_str
        assert "Rate limit exceeded" in error_str
    
    def test_quota_exceeded_error_with_retry_info(self):
        """Test QuotaExceededError with retry information."""
        error = QuotaExceededError(
            "Quota exceeded",
            api_name="Test API",
            quota_type="daily",
            retry_delay_seconds=60,
            reset_time="2024-01-01T12:00:00Z"
        )
        
        error_str = str(error)
        assert "Quota exceeded" in error_str
        assert "API: Test API" in error_str
        assert "Quota Type: daily" in error_str
        assert "Retry After: 60s" in error_str
        assert "Resets: 2024-01-01T12:00:00Z" in error_str
    
    def test_video_unavailable_error_with_video_id(self):
        """Test VideoUnavailableError with video ID context."""
        error = VideoUnavailableError(
            "Video is private",
            video_id="dQw4w9WgXcQ",
            details="Video owner has set it to private"
        )
        
        error_str = str(error)
        assert "Video is private" in error_str
        assert "Video ID: dQw4w9WgXcQ" in error_str
        assert "Video owner has set it to private" in error_str
    
    def test_invalid_url_error_with_details(self):
        """Test InvalidURLError with detailed information."""
        error = InvalidURLError(
            "URL is not from a supported YouTube domain",
            details="Domain: vimeo.com, Supported: youtube.com, www.youtube.com, m.youtube.com, youtu.be"
        )
        
        error_str = str(error)
        assert "URL is not from a supported YouTube domain" in error_str
        assert "Domain: vimeo.com" in error_str
        assert "Supported: youtube.com" in error_str


class TestRetryLogicAndFallbacks:
    """Test retry logic and fallback mechanisms."""
    
    def test_retry_logic_with_exponential_backoff(self):
        """Test that retry logic uses exponential backoff."""
        writer = GeminiSummaryWriter("test_key", max_retries=3)
        
        # Mock the API call to fail multiple times
        mock_func = Mock()
        mock_func.side_effect = [
            APIError("Temporary error", api_name="Test API"),
            APIError("Temporary error", api_name="Test API"),
            "Success"
        ]
        
        with patch('src.youtube_notion.writers.gemini_summary_writer.time.sleep') as mock_sleep:
            result = writer._api_call_with_retry(mock_func)
        
        assert result == "Success"
        assert mock_func.call_count == 3
        assert mock_sleep.call_count == 2  # Two retry delays
        
        # Verify exponential backoff (first call should be ~1s, second ~2s)
        sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
        assert sleep_calls[0] < sleep_calls[1]  # Second delay should be longer
    
    def test_non_retryable_errors_not_retried(self):
        """Test that non-retryable errors are not retried."""
        writer = GeminiSummaryWriter("test_key", max_retries=3)
        
        # Mock the API call to fail with authentication error
        mock_func = Mock()
        mock_func.side_effect = APIError("Invalid API key", api_name="Test API")
        
        with patch('src.youtube_notion.writers.gemini_summary_writer.time.sleep') as mock_sleep:
            with pytest.raises(APIError):
                writer._api_call_with_retry(mock_func)
        
        assert mock_func.call_count == 1  # Should not retry
        assert mock_sleep.call_count == 0  # No retry delays
    
    def test_quota_error_with_retry_delay(self):
        """Test quota error handling with retry delay."""
        writer = GeminiSummaryWriter("test_key", max_retries=2)
        
        # Mock the API call to fail with quota error that has retry delay
        quota_error = QuotaExceededError(
            "Quota exceeded",
            api_name="Test API",
            retry_delay_seconds=30
        )
        
        mock_func = Mock()
        mock_func.side_effect = [quota_error, "Success"]
        
        with patch('src.youtube_notion.writers.gemini_summary_writer.time.sleep') as mock_sleep:
            with patch('src.youtube_notion.writers.gemini_summary_writer.os.environ', {'PYTEST_CURRENT_TEST': 'test'}):
                result = writer._api_call_with_retry(mock_func)
        
        assert result == "Success"
        assert mock_func.call_count == 2
        assert mock_sleep.call_count == 1
        
        # In test mode, delay should be capped at 5 seconds
        sleep_delay = mock_sleep.call_args_list[0][0][0]
        assert sleep_delay <= 5
    
    def test_fallback_from_api_to_web_scraping(self):
        """Test fallback from YouTube API to web scraping."""
        # This would be tested in integration tests with actual API mocking
        # Here we just verify the structure exists
        extractor = VideoMetadataExtractor(youtube_api_key="test_key")
        
        # Verify that both methods exist
        assert hasattr(extractor, '_get_metadata_via_api')
        assert hasattr(extractor, '_get_metadata_via_scraping')
        assert hasattr(extractor, '_get_video_metadata')