"""
Unit tests for VideoProcessor orchestrator.

This module tests the VideoProcessor class that coordinates all components
of the video processing pipeline using mock implementations to avoid
external dependencies.
"""

import pytest
from typing import Dict, Any, Optional
from unittest.mock import Mock

from src.youtube_notion.processors.video_processor import VideoProcessor
from src.youtube_notion.interfaces import SummaryWriter, Storage
from src.youtube_notion.extractors.video_metadata_extractor import VideoMetadataExtractor
from src.youtube_notion.utils.exceptions import (
    VideoProcessingError,
    ConfigurationError,
    MetadataExtractionError,
    SummaryGenerationError,
    StorageError
)


class MockVideoMetadataExtractor:
    """Mock implementation of VideoMetadataExtractor for testing."""
    
    def __init__(self, should_fail: bool = False, metadata: Optional[Dict[str, Any]] = None):
        """
        Initialize mock extractor.
        
        Args:
            should_fail: If True, extract_metadata will raise an exception
            metadata: Custom metadata to return, uses default if None
        """
        self.should_fail = should_fail
        self.metadata = metadata or {
            "title": "Test Video Title",
            "channel": "Test Channel",
            "description": "Test video description",
            "published_at": "2024-01-01T00:00:00Z",
            "thumbnail_url": "https://img.youtube.com/vi/test123/maxresdefault.jpg",
            "video_id": "test123"
        }
        self.calls = []
    
    def extract_metadata(self, video_url: str) -> Dict[str, Any]:
        """Mock metadata extraction."""
        self.calls.append(video_url)
        
        if self.should_fail:
            raise MetadataExtractionError("Mock extraction failure")
        
        return self.metadata.copy()


class MockSummaryWriter(SummaryWriter):
    """Mock implementation of SummaryWriter for testing."""
    
    def __init__(self, should_fail: bool = False, summary: str = "Mock summary content"):
        """
        Initialize mock summary writer.
        
        Args:
            should_fail: If True, methods will raise exceptions
            summary: Summary content to return
        """
        self.should_fail = should_fail
        self.summary = summary
        self.calls = []
        self.config_valid = True
    
    def generate_summary(self, video_url: str, video_metadata: Dict[str, Any], 
                        custom_prompt: Optional[str] = None) -> str:
        """Mock summary generation."""
        self.calls.append((video_url, video_metadata, custom_prompt))
        
        if self.should_fail:
            raise SummaryGenerationError("Mock summary generation failure")
        
        return self.summary
    
    def validate_configuration(self) -> bool:
        """Mock configuration validation."""
        if self.should_fail:
            raise ConfigurationError("Mock configuration error")
        
        return self.config_valid


class MockStorage(Storage):
    """Mock implementation of Storage for testing."""
    
    def __init__(self, should_fail: bool = False):
        """
        Initialize mock storage.
        
        Args:
            should_fail: If True, methods will raise exceptions or return False
        """
        self.should_fail = should_fail
        self.stored_videos = []
        self.config_valid = True
    
    def store_video_summary(self, video_data: Dict[str, Any]) -> bool:
        """Mock video storage."""
        if self.should_fail:
            if hasattr(self, 'raise_exception') and self.raise_exception:
                raise StorageError("Mock storage failure")
            return False
        
        self.stored_videos.append(video_data.copy())
        return True
    
    def validate_configuration(self) -> bool:
        """Mock configuration validation."""
        if self.should_fail:
            raise ConfigurationError("Mock storage configuration error")
        
        return self.config_valid
    
    def find_target_location(self) -> Optional[str]:
        """Mock target location finding."""
        if self.should_fail:
            return None
        
        return "mock-database-id"


class TestVideoProcessorInitialization:
    """Test VideoProcessor initialization and validation."""
    
    def test_successful_initialization(self):
        """Test successful initialization with valid components."""
        extractor = MockVideoMetadataExtractor()
        writer = MockSummaryWriter()
        storage = MockStorage()
        
        processor = VideoProcessor(extractor, writer, storage)
        
        assert processor.metadata_extractor is extractor
        assert processor.summary_writer is writer
        assert processor.storage is storage
    
    def test_initialization_with_none_extractor(self):
        """Test initialization fails with None metadata extractor."""
        writer = MockSummaryWriter()
        storage = MockStorage()
        
        with pytest.raises(ConfigurationError, match="VideoMetadataExtractor is required"):
            VideoProcessor(None, writer, storage)
    
    def test_initialization_with_none_writer(self):
        """Test initialization fails with None summary writer."""
        extractor = MockVideoMetadataExtractor()
        storage = MockStorage()
        
        with pytest.raises(ConfigurationError, match="SummaryWriter is required"):
            VideoProcessor(extractor, None, storage)
    
    def test_initialization_with_none_storage(self):
        """Test initialization fails with None storage."""
        extractor = MockVideoMetadataExtractor()
        writer = MockSummaryWriter()
        
        with pytest.raises(ConfigurationError, match="Storage is required"):
            VideoProcessor(extractor, writer, None)


class TestVideoProcessorProcessVideo:
    """Test VideoProcessor.process_video method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MockVideoMetadataExtractor()
        self.writer = MockSummaryWriter()
        self.storage = MockStorage()
        self.processor = VideoProcessor(self.extractor, self.writer, self.storage)
    
    def test_successful_video_processing(self):
        """Test successful video processing through complete pipeline."""
        video_url = "https://youtube.com/watch?v=test123"
        custom_prompt = "Custom test prompt"
        
        result = self.processor.process_video(video_url, custom_prompt)
        
        # Verify success
        assert result is True
        
        # Verify metadata extractor was called
        assert len(self.extractor.calls) == 1
        assert self.extractor.calls[0] == video_url
        
        # Verify summary writer was called with correct parameters
        assert len(self.writer.calls) == 1
        call_args = self.writer.calls[0]
        assert call_args[0] == video_url
        assert call_args[1] == self.extractor.metadata
        assert call_args[2] == custom_prompt
        
        # Verify storage was called with correct data structure
        assert len(self.storage.stored_videos) == 1
        stored_data = self.storage.stored_videos[0]
        
        expected_data = {
            "Title": "Test Video Title",
            "Channel": "Test Channel",
            "Video URL": video_url,
            "Cover": "https://img.youtube.com/vi/test123/maxresdefault.jpg",
            "Summary": "Mock summary content",
            "Description": "Test video description",
            "Published": "2024-01-01T00:00:00Z",
            "Video ID": "test123"
        }
        
        assert stored_data == expected_data
    
    def test_video_processing_without_custom_prompt(self):
        """Test video processing without custom prompt."""
        video_url = "https://youtube.com/watch?v=test123"
        
        result = self.processor.process_video(video_url)
        
        assert result is True
        
        # Verify summary writer was called with None for custom_prompt
        assert len(self.writer.calls) == 1
        call_args = self.writer.calls[0]
        assert call_args[2] is None
    
    def test_video_processing_with_minimal_metadata(self):
        """Test video processing with minimal metadata."""
        # Set up extractor with minimal metadata
        minimal_metadata = {
            "title": "Minimal Title",
            "channel": "Minimal Channel"
        }
        self.extractor.metadata = minimal_metadata
        
        video_url = "https://youtube.com/watch?v=test123"
        result = self.processor.process_video(video_url)
        
        assert result is True
        
        # Verify storage received data with defaults for missing fields
        stored_data = self.storage.stored_videos[0]
        assert stored_data["Title"] == "Minimal Title"
        assert stored_data["Channel"] == "Minimal Channel"
        assert stored_data["Cover"] == ""  # Default for missing thumbnail_url
        assert "Description" not in stored_data  # Not added if not in metadata
        assert "Published" not in stored_data  # Not added if not in metadata
        assert "Video ID" not in stored_data  # Not added if not in metadata
    
    def test_video_processing_with_invalid_url(self):
        """Test video processing with invalid URL."""
        with pytest.raises(VideoProcessingError, match="Video URL must be a non-empty string"):
            self.processor.process_video("")
        
        with pytest.raises(VideoProcessingError, match="Video URL must be a non-empty string"):
            self.processor.process_video(None)
        
        with pytest.raises(VideoProcessingError, match="Video URL must be a non-empty string"):
            self.processor.process_video(123)
    
    def test_video_processing_metadata_extraction_failure(self):
        """Test video processing when metadata extraction fails."""
        self.extractor.should_fail = True
        
        with pytest.raises(MetadataExtractionError, match="Mock extraction failure"):
            self.processor.process_video("https://youtube.com/watch?v=test123")
        
        # Verify no further processing occurred
        assert len(self.writer.calls) == 0
        assert len(self.storage.stored_videos) == 0
    
    def test_video_processing_summary_generation_failure(self):
        """Test video processing when summary generation fails."""
        self.writer.should_fail = True
        
        with pytest.raises(SummaryGenerationError, match="Mock summary generation failure"):
            self.processor.process_video("https://youtube.com/watch?v=test123")
        
        # Verify metadata extraction occurred but storage did not
        assert len(self.extractor.calls) == 1
        assert len(self.writer.calls) == 1
        assert len(self.storage.stored_videos) == 0
    
    def test_video_processing_storage_failure_with_exception(self):
        """Test video processing when storage fails with exception."""
        self.storage.should_fail = True
        self.storage.raise_exception = True
        
        with pytest.raises(StorageError, match="Mock storage failure"):
            self.processor.process_video("https://youtube.com/watch?v=test123")
        
        # Verify all steps up to storage occurred
        assert len(self.extractor.calls) == 1
        assert len(self.writer.calls) == 1
        assert len(self.storage.stored_videos) == 0
    
    def test_video_processing_storage_failure_with_false_return(self):
        """Test video processing when storage returns False."""
        self.storage.should_fail = True
        # Don't set raise_exception, so it returns False instead
        
        with pytest.raises(StorageError, match="Storage operation returned failure status"):
            self.processor.process_video("https://youtube.com/watch?v=test123")
        
        # Verify all steps occurred but storage returned failure
        assert len(self.extractor.calls) == 1
        assert len(self.writer.calls) == 1
        assert len(self.storage.stored_videos) == 0
    
    def test_video_processing_unexpected_error(self):
        """Test video processing handles unexpected errors."""
        # Create a mock that raises an unexpected error
        self.extractor.extract_metadata = Mock(side_effect=ValueError("Unexpected error"))
        
        with pytest.raises(VideoProcessingError, match="Unexpected error during video processing"):
            self.processor.process_video("https://youtube.com/watch?v=test123")


class TestVideoProcessorValidateConfiguration:
    """Test VideoProcessor.validate_configuration method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MockVideoMetadataExtractor()
        self.writer = MockSummaryWriter()
        self.storage = MockStorage()
        self.processor = VideoProcessor(self.extractor, self.writer, self.storage)
    
    def test_successful_configuration_validation(self):
        """Test successful configuration validation."""
        result = self.processor.validate_configuration()
        
        assert result is True
    
    def test_configuration_validation_writer_failure(self):
        """Test configuration validation when summary writer fails."""
        self.writer.should_fail = True
        
        with pytest.raises(ConfigurationError) as exc_info:
            self.processor.validate_configuration()
        
        assert "SummaryWriter: Mock configuration error" in str(exc_info.value)
    
    def test_configuration_validation_storage_failure(self):
        """Test configuration validation when storage fails."""
        self.storage.should_fail = True
        
        with pytest.raises(ConfigurationError) as exc_info:
            self.processor.validate_configuration()
        
        assert "Storage: Mock storage configuration error" in str(exc_info.value)
    
    def test_configuration_validation_multiple_failures(self):
        """Test configuration validation with multiple component failures."""
        self.writer.should_fail = True
        self.storage.should_fail = True
        
        with pytest.raises(ConfigurationError) as exc_info:
            self.processor.validate_configuration()
        
        error_message = str(exc_info.value)
        assert "SummaryWriter: Mock configuration error" in error_message
        assert "Storage: Mock storage configuration error" in error_message
    
    def test_configuration_validation_writer_returns_false(self):
        """Test configuration validation when writer returns False."""
        self.writer.config_valid = False
        
        with pytest.raises(ConfigurationError) as exc_info:
            self.processor.validate_configuration()
        
        assert "SummaryWriter: configuration validation failed" in str(exc_info.value)
    
    def test_configuration_validation_storage_returns_false(self):
        """Test configuration validation when storage returns False."""
        self.storage.config_valid = False
        
        with pytest.raises(ConfigurationError) as exc_info:
            self.processor.validate_configuration()
        
        assert "Storage: configuration validation failed" in str(exc_info.value)
    
    def test_configuration_validation_extractor_missing_method(self):
        """Test configuration validation when extractor is missing required method."""
        # Create a mock extractor without the extract_metadata method
        invalid_extractor = Mock()
        del invalid_extractor.extract_metadata
        
        processor = VideoProcessor(invalid_extractor, self.writer, self.storage)
        
        with pytest.raises(ConfigurationError) as exc_info:
            processor.validate_configuration()
        
        assert "VideoMetadataExtractor: missing extract_metadata method" in str(exc_info.value)


class TestVideoProcessorGetComponentInfo:
    """Test VideoProcessor.get_component_info method."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = MockVideoMetadataExtractor()
        self.writer = MockSummaryWriter()
        self.storage = MockStorage()
        self.processor = VideoProcessor(self.extractor, self.writer, self.storage)
    
    def test_get_component_info_success(self):
        """Test getting component info with valid configuration."""
        info = self.processor.get_component_info()
        
        expected_info = {
            "metadata_extractor": "MockVideoMetadataExtractor",
            "summary_writer": "MockSummaryWriter",
            "storage": "MockStorage",
            "configuration_status": "valid"
        }
        
        assert info == expected_info
    
    def test_get_component_info_invalid_configuration(self):
        """Test getting component info with invalid configuration."""
        self.writer.should_fail = True
        
        info = self.processor.get_component_info()
        
        assert info["metadata_extractor"] == "MockVideoMetadataExtractor"
        assert info["summary_writer"] == "MockSummaryWriter"
        assert info["storage"] == "MockStorage"
        assert info["configuration_status"].startswith("invalid:")
        assert "Component configuration validation failed" in info["configuration_status"]
    
    def test_get_component_info_unexpected_error(self):
        """Test getting component info when validation raises unexpected error."""
        # Mock validate_configuration to raise an unexpected error
        self.processor.validate_configuration = Mock(side_effect=ValueError("Unexpected"))
        
        info = self.processor.get_component_info()
        
        assert info["configuration_status"].startswith("error:")
        assert "Unexpected" in info["configuration_status"]


class TestVideoProcessorIntegration:
    """Integration tests for VideoProcessor with realistic scenarios."""
    
    def test_complete_workflow_with_real_like_data(self):
        """Test complete workflow with realistic video data."""
        # Set up realistic metadata
        realistic_metadata = {
            "title": "How to Build a REST API with Python Flask",
            "channel": "Programming with Mosh",
            "description": "Learn how to build a REST API using Python Flask framework...",
            "published_at": "2024-01-15T10:30:00Z",
            "thumbnail_url": "https://img.youtube.com/vi/abc123def/maxresdefault.jpg",
            "video_id": "abc123def"
        }
        
        extractor = MockVideoMetadataExtractor(metadata=realistic_metadata)
        writer = MockSummaryWriter(summary="# Flask REST API Tutorial\n\n## Overview\nThis video covers...")
        storage = MockStorage()
        
        processor = VideoProcessor(extractor, writer, storage)
        
        # Process video
        result = processor.process_video(
            "https://youtube.com/watch?v=abc123def",
            "Please focus on the key concepts and provide code examples"
        )
        
        assert result is True
        
        # Verify stored data structure
        stored_data = storage.stored_videos[0]
        assert stored_data["Title"] == realistic_metadata["title"]
        assert stored_data["Channel"] == realistic_metadata["channel"]
        assert stored_data["Description"] == realistic_metadata["description"]
        assert stored_data["Published"] == realistic_metadata["published_at"]
        assert stored_data["Video ID"] == realistic_metadata["video_id"]
        assert stored_data["Summary"].startswith("# Flask REST API Tutorial")
    
    def test_error_recovery_scenarios(self):
        """Test various error scenarios and recovery."""
        extractor = MockVideoMetadataExtractor()
        writer = MockSummaryWriter()
        storage = MockStorage()
        
        processor = VideoProcessor(extractor, writer, storage)
        
        # Test with different error conditions
        test_cases = [
            (MetadataExtractionError, lambda: setattr(extractor, 'should_fail', True)),
            (SummaryGenerationError, lambda: setattr(writer, 'should_fail', True)),
            (StorageError, lambda: (setattr(storage, 'should_fail', True), setattr(storage, 'raise_exception', True))[1])
        ]
        
        for expected_error, setup_error in test_cases:
            # Reset components
            extractor.should_fail = False
            writer.should_fail = False
            storage.should_fail = False
            if hasattr(storage, 'raise_exception'):
                delattr(storage, 'raise_exception')
            
            # Set up specific error
            setup_error()
            
            # Verify error is raised
            with pytest.raises(expected_error):
                processor.process_video("https://youtube.com/watch?v=test123")