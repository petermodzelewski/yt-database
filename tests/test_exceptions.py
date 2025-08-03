"""
Unit tests for exception hierarchy.

This module tests the custom exception classes to ensure they provide
proper error handling capabilities and maintain the expected hierarchy.
"""

import pytest

from src.youtube_notion.utils.exceptions import (
    VideoProcessingError,
    ConfigurationError,
    MetadataExtractionError,
    SummaryGenerationError,
    StorageError
)


class TestVideoProcessingError:
    """Test the base VideoProcessingError class."""
    
    def test_basic_initialization(self):
        """Test basic exception initialization."""
        error = VideoProcessingError("Test error")
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.details is None
    
    def test_initialization_with_details(self):
        """Test exception initialization with details."""
        error = VideoProcessingError("Test error", "Additional details")
        expected_str = "Test error\nDetails: Additional details"
        assert str(error) == expected_str
        assert error.message == "Test error"
        assert error.details == "Additional details"
    
    def test_is_exception(self):
        """Test that VideoProcessingError is a proper exception."""
        error = VideoProcessingError("Test")
        assert isinstance(error, Exception)
    
    def test_can_be_raised_and_caught(self):
        """Test that the exception can be raised and caught."""
        with pytest.raises(VideoProcessingError) as exc_info:
            raise VideoProcessingError("Test error", "Test details")
        
        assert exc_info.value.message == "Test error"
        assert exc_info.value.details == "Test details"


class TestExceptionHierarchy:
    """Test the exception hierarchy relationships."""
    
    def test_configuration_error_inheritance(self):
        """Test ConfigurationError inherits from VideoProcessingError."""
        error = ConfigurationError("Config error")
        assert isinstance(error, VideoProcessingError)
        assert isinstance(error, Exception)
    
    def test_metadata_extraction_error_inheritance(self):
        """Test MetadataExtractionError inherits from VideoProcessingError."""
        error = MetadataExtractionError("Metadata error")
        assert isinstance(error, VideoProcessingError)
        assert isinstance(error, Exception)
    
    def test_summary_generation_error_inheritance(self):
        """Test SummaryGenerationError inherits from VideoProcessingError."""
        error = SummaryGenerationError("Summary error")
        assert isinstance(error, VideoProcessingError)
        assert isinstance(error, Exception)
    
    def test_storage_error_inheritance(self):
        """Test StorageError inherits from VideoProcessingError."""
        error = StorageError("Storage error")
        assert isinstance(error, VideoProcessingError)
        assert isinstance(error, Exception)


class TestSpecificExceptions:
    """Test specific exception types."""
    
    def test_configuration_error(self):
        """Test ConfigurationError functionality."""
        error = ConfigurationError("Missing API key", "GEMINI_API_KEY not found")
        assert error.message == "Missing API key"
        assert error.details == "GEMINI_API_KEY not found"
        
        with pytest.raises(ConfigurationError):
            raise error
    
    def test_metadata_extraction_error(self):
        """Test MetadataExtractionError functionality."""
        error = MetadataExtractionError("Invalid URL", "URL format not recognized")
        assert error.message == "Invalid URL"
        assert error.details == "URL format not recognized"
        
        with pytest.raises(MetadataExtractionError):
            raise error
    
    def test_summary_generation_error(self):
        """Test SummaryGenerationError functionality."""
        error = SummaryGenerationError("API quota exceeded", "Rate limit: 100 requests/day")
        assert error.message == "API quota exceeded"
        assert error.details == "Rate limit: 100 requests/day"
        
        with pytest.raises(SummaryGenerationError):
            raise error
    
    def test_storage_error(self):
        """Test StorageError functionality."""
        error = StorageError("Database connection failed", "Connection timeout after 30s")
        assert error.message == "Database connection failed"
        assert error.details == "Connection timeout after 30s"
        
        with pytest.raises(StorageError):
            raise error


class TestExceptionCatching:
    """Test exception catching patterns."""
    
    def test_catch_base_exception(self):
        """Test catching specific exceptions with base class."""
        with pytest.raises(VideoProcessingError):
            raise ConfigurationError("Config error")
        
        with pytest.raises(VideoProcessingError):
            raise MetadataExtractionError("Metadata error")
        
        with pytest.raises(VideoProcessingError):
            raise SummaryGenerationError("Summary error")
        
        with pytest.raises(VideoProcessingError):
            raise StorageError("Storage error")
    
    def test_catch_specific_exceptions(self):
        """Test catching specific exception types."""
        # Test that we can catch specific types
        try:
            raise ConfigurationError("Config error")
        except ConfigurationError as e:
            assert e.message == "Config error"
        except VideoProcessingError:
            pytest.fail("Should have caught ConfigurationError specifically")
        
        try:
            raise StorageError("Storage error")
        except StorageError as e:
            assert e.message == "Storage error"
        except VideoProcessingError:
            pytest.fail("Should have caught StorageError specifically")
    
    def test_exception_chaining(self):
        """Test that exceptions can be chained properly."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ConfigurationError("Config failed") from e
        except ConfigurationError as e:
            assert e.message == "Config failed"
            assert isinstance(e.__cause__, ValueError)
            assert str(e.__cause__) == "Original error"