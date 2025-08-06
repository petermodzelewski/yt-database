"""
Unit tests for component integration using mock implementations.

This module tests the complete video processing workflow using mock
implementations to ensure components work together correctly without
external dependencies.
"""

import pytest
from typing import Dict, Any

from tests.fixtures.mock_implementations import (
    MockSummaryWriter,
    MockStorage,
    MockMetadataExtractor,
    create_successful_mocks,
    create_failing_mocks
)
from src.youtube_notion.processors.video_processor import VideoProcessor
from src.youtube_notion.utils.exceptions import (
    MetadataExtractionError,
    SummaryGenerationError,
    StorageError,
    ConfigurationError,
    VideoProcessingError
)


class TestComponentIntegration:
    """Test integration between components using mocks."""
    
    def test_successful_video_processing_workflow(self):
        """Test complete successful video processing workflow."""
        # Create successful mocks
        extractor, writer, storage = create_successful_mocks()
        
        # Create processor with mocks
        processor = VideoProcessor(extractor, writer, storage)
        
        # Process a video
        test_url = "https://youtu.be/test123"
        result = processor.process_video(test_url)
        
        # Verify success
        assert result is True
        
        # Verify all components were called
        assert len(extractor.extract_metadata_calls) == 1
        assert len(writer.generate_summary_calls) == 1
        assert len(storage.store_video_summary_calls) == 1
        
        # Verify data flow
        assert extractor.extract_metadata_calls[0] == test_url
        
        # Verify summary writer received metadata
        summary_call = writer.generate_summary_calls[0]
        assert summary_call[0] == test_url
        assert summary_call[1]['video_id'] == 'test123'
        
        # Verify storage received processed data
        stored_data = storage.store_video_summary_calls[0]
        assert stored_data['Title'] == 'Mock Video for test123'
        assert stored_data['Video URL'] == test_url
        assert 'MockSummaryWriter' in stored_data['Summary']
    
    def test_video_processing_with_custom_prompt(self):
        """Test video processing with custom prompt."""
        extractor, writer, storage = create_successful_mocks()
        processor = VideoProcessor(extractor, writer, storage)
        
        test_url = "https://youtu.be/test123"
        custom_prompt = "Create a detailed technical summary"
        
        result = processor.process_video(test_url, custom_prompt)
        
        assert result is True
        
        # Verify custom prompt was passed to summary writer
        summary_call = writer.generate_summary_calls[0]
        assert summary_call[2] == custom_prompt
    
    def test_configuration_validation_success(self):
        """Test successful configuration validation."""
        extractor, writer, storage = create_successful_mocks()
        processor = VideoProcessor(extractor, writer, storage)
        
        # All mocks are configured to be valid
        assert processor.validate_configuration() is True
        
        # Verify all components were validated
        assert len(writer.validate_configuration_calls) == 1
        assert len(storage.validate_configuration_calls) == 1
    
    def test_configuration_validation_failure(self):
        """Test configuration validation with invalid components."""
        extractor = MockMetadataExtractor()
        writer = MockSummaryWriter(configuration_valid=False)
        storage = MockStorage(configuration_valid=False)
        
        processor = VideoProcessor(extractor, writer, storage)
        
        # Should raise ConfigurationError
        with pytest.raises(ConfigurationError):
            processor.validate_configuration()
    
    def test_metadata_extraction_failure(self):
        """Test handling of metadata extraction failure."""
        extractor = MockMetadataExtractor(should_fail=True)
        writer = MockSummaryWriter()
        storage = MockStorage()
        
        processor = VideoProcessor(extractor, writer, storage)
        
        test_url = "https://youtu.be/test123"
        
        with pytest.raises(MetadataExtractionError):
            processor.process_video(test_url)
        
        # Verify only metadata extraction was attempted
        assert len(extractor.extract_metadata_calls) == 1
        assert len(writer.generate_summary_calls) == 0
        assert len(storage.store_video_summary_calls) == 0
    
    def test_summary_generation_failure(self):
        """Test handling of summary generation failure."""
        extractor = MockMetadataExtractor()
        writer = MockSummaryWriter(should_fail=True)
        storage = MockStorage()
        
        processor = VideoProcessor(extractor, writer, storage)
        
        test_url = "https://youtu.be/test123"
        
        with pytest.raises(SummaryGenerationError):
            processor.process_video(test_url)
        
        # Verify metadata extraction succeeded but summary generation failed
        assert len(extractor.extract_metadata_calls) == 1
        assert len(writer.generate_summary_calls) == 1
        assert len(storage.store_video_summary_calls) == 0
    
    def test_storage_failure(self):
        """Test handling of storage failure."""
        extractor = MockMetadataExtractor()
        writer = MockSummaryWriter()
        storage = MockStorage(should_fail=True)
        
        processor = VideoProcessor(extractor, writer, storage)
        
        test_url = "https://youtu.be/test123"
        
        with pytest.raises(StorageError):
            processor.process_video(test_url)
        
        # Verify all steps were attempted
        assert len(extractor.extract_metadata_calls) == 1
        assert len(writer.generate_summary_calls) == 1
        assert len(storage.store_video_summary_calls) == 1
    
    def test_invalid_configuration_prevents_processing(self):
        """Test that invalid configuration prevents processing."""
        extractor = MockMetadataExtractor()
        writer = MockSummaryWriter(configuration_valid=False)
        storage = MockStorage()
        
        processor = VideoProcessor(extractor, writer, storage)
        
        test_url = "https://youtu.be/test123"
        
        # Should raise configuration error during processing (wrapped in VideoProcessingError)
        with pytest.raises((ConfigurationError, VideoProcessingError)):
            processor.process_video(test_url)
    
    def test_data_transformation_through_pipeline(self):
        """Test that data is correctly transformed through the pipeline."""
        # Create mocks with specific responses
        extractor = MockMetadataExtractor()
        writer = MockSummaryWriter()
        storage = MockStorage()
        
        # Configure custom metadata
        test_url = "https://youtu.be/custom123"
        custom_metadata = {
            'title': 'Custom Test Video',
            'channel': 'Custom Channel',
            'description': 'Custom description',
            'thumbnail_url': 'https://img.youtube.com/vi/custom123/maxresdefault.jpg'
        }
        extractor.set_metadata_for_url(test_url, custom_metadata)
        
        # Configure custom summary
        custom_summary = "# Custom Summary\n\nThis is a custom test summary."
        writer.set_response_for_url(test_url, custom_summary)
        
        processor = VideoProcessor(extractor, writer, storage)
        
        result = processor.process_video(test_url)
        assert result is True
        
        # Verify data transformation
        stored_data = storage.stored_videos[0]
        assert stored_data['Title'] == 'Custom Test Video'
        assert stored_data['Channel'] == 'Custom Channel'
        assert stored_data['Video URL'] == test_url
        assert stored_data['Summary'] == custom_summary
        assert 'custom123' in stored_data['Cover']
    
    def test_multiple_video_processing(self):
        """Test processing multiple videos in sequence."""
        extractor, writer, storage = create_successful_mocks()
        processor = VideoProcessor(extractor, writer, storage)
        
        test_urls = [
            "https://youtu.be/video1",
            "https://youtu.be/video2",
            "https://youtu.be/video3"
        ]
        
        results = []
        for url in test_urls:
            result = processor.process_video(url)
            results.append(result)
        
        # All should succeed
        assert all(results)
        
        # Verify all videos were processed
        assert len(extractor.extract_metadata_calls) == 3
        assert len(writer.generate_summary_calls) == 3
        assert len(storage.store_video_summary_calls) == 3
        assert len(storage.stored_videos) == 3
        
        # Verify each video was processed with correct URL
        for i, url in enumerate(test_urls):
            assert extractor.extract_metadata_calls[i] == url
            assert writer.generate_summary_calls[i][0] == url
            assert storage.stored_videos[i]['Video URL'] == url
    
    def test_component_isolation(self):
        """Test that component failures don't affect other components."""
        # Create mocks where different components fail for different URLs
        extractor = MockMetadataExtractor(fail_on_urls=["https://youtu.be/extract_fail"])
        writer = MockSummaryWriter(fail_on_urls=["https://youtu.be/summary_fail"])
        storage = MockStorage(fail_on_titles=["Storage Fail Video"])
        
        processor = VideoProcessor(extractor, writer, storage)
        
        # Test metadata extraction failure
        with pytest.raises(MetadataExtractionError):
            processor.process_video("https://youtu.be/extract_fail")
        
        # Test summary generation failure
        with pytest.raises(SummaryGenerationError):
            processor.process_video("https://youtu.be/summary_fail")
        
        # Test storage failure
        # First configure a custom title that will trigger storage failure
        storage_fail_url = "https://youtu.be/storage_fail"
        extractor.set_metadata_for_url(storage_fail_url, {'title': 'Storage Fail Video'})
        
        with pytest.raises(StorageError):
            processor.process_video(storage_fail_url)
        
        # Test successful processing still works
        success_result = processor.process_video("https://youtu.be/success")
        assert success_result is True
        
        # Verify that successful operations were tracked despite failures
        assert len(storage.stored_videos) == 1  # Only the successful one
        assert storage.stored_videos[0]['Video URL'] == "https://youtu.be/success"