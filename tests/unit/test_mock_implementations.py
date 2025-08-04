"""
Tests for mock implementations.

This module tests the mock implementations to ensure they behave correctly
and provide the expected functionality for unit testing scenarios.
"""

import pytest
from typing import Dict, Any

from tests.fixtures.mock_implementations import (
    MockSummaryWriter,
    MockStorage,
    MockMetadataExtractor,
    create_successful_mocks,
    create_failing_mocks,
    create_mixed_mocks
)
from src.youtube_notion.utils.exceptions import (
    SummaryGenerationError,
    StorageError,
    ConfigurationError,
    MetadataExtractionError,
    InvalidURLError
)


class TestMockSummaryWriter:
    """Test the MockSummaryWriter implementation."""
    
    def test_successful_summary_generation(self):
        """Test successful summary generation with default response."""
        mock = MockSummaryWriter()
        
        video_url = "https://youtu.be/test123"
        video_metadata = {
            'title': 'Test Video',
            'channel': 'Test Channel',
            'description': 'Test description'
        }
        
        summary = mock.generate_summary(video_url, video_metadata)
        
        # Verify response contains expected content
        assert "Test Video" in summary
        assert "Test Channel" in summary
        assert "MockSummaryWriter" in summary
        
        # Verify call tracking
        assert len(mock.generate_summary_calls) == 1
        call_args = mock.generate_summary_calls[0]
        assert call_args[0] == video_url
        assert call_args[1] == video_metadata
        assert call_args[2] is None  # No custom prompt
    
    def test_custom_response_for_url(self):
        """Test custom response configuration for specific URLs."""
        custom_response = "# Custom Test Summary\n\nThis is a custom response."
        mock = MockSummaryWriter(responses={
            "https://youtu.be/custom123": custom_response
        })
        
        video_metadata = {'title': 'Test', 'channel': 'Test'}
        
        # Test custom response
        summary = mock.generate_summary("https://youtu.be/custom123", video_metadata)
        assert summary == custom_response
        
        # Test default response for different URL
        default_summary = mock.generate_summary("https://youtu.be/other123", video_metadata)
        assert default_summary != custom_response
        assert "MockSummaryWriter" in default_summary
    
    def test_custom_prompt_handling(self):
        """Test handling of custom prompts."""
        mock = MockSummaryWriter()
        
        video_url = "https://youtu.be/test123"
        video_metadata = {'title': 'Test Video', 'channel': 'Test Channel'}
        custom_prompt = "Generate a detailed technical summary"
        
        summary = mock.generate_summary(video_url, video_metadata, custom_prompt)
        
        # Verify custom prompt is included in response
        assert custom_prompt in summary
        
        # Verify call tracking includes custom prompt
        assert len(mock.generate_summary_calls) == 1
        call_args = mock.generate_summary_calls[0]
        assert call_args[2] == custom_prompt
    
    def test_failure_simulation(self):
        """Test failure simulation for error handling tests."""
        mock = MockSummaryWriter(should_fail=True)
        
        video_metadata = {'title': 'Test', 'channel': 'Test'}
        
        with pytest.raises(SummaryGenerationError) as exc_info:
            mock.generate_summary("https://youtu.be/test123", video_metadata)
        
        assert "Mock summary generation failed" in str(exc_info.value)
        
        # Verify call was still tracked
        assert len(mock.generate_summary_calls) == 1
    
    def test_url_specific_failures(self):
        """Test URL-specific failure configuration."""
        fail_url = "https://youtu.be/fail123"
        mock = MockSummaryWriter(fail_on_urls=[fail_url])
        
        video_metadata = {'title': 'Test', 'channel': 'Test'}
        
        # Should fail for specific URL
        with pytest.raises(SummaryGenerationError):
            mock.generate_summary(fail_url, video_metadata)
        
        # Should succeed for other URLs
        summary = mock.generate_summary("https://youtu.be/success123", video_metadata)
        assert "MockSummaryWriter" in summary
    
    def test_configuration_validation(self):
        """Test configuration validation behavior."""
        # Valid configuration
        mock = MockSummaryWriter(configuration_valid=True)
        assert mock.validate_configuration() is True
        assert len(mock.validate_configuration_calls) == 1
        
        # Invalid configuration
        mock = MockSummaryWriter(configuration_valid=False)
        assert mock.validate_configuration() is False
        
        # Should raise error during summary generation
        with pytest.raises(ConfigurationError):
            mock.generate_summary("https://youtu.be/test", {'title': 'Test', 'channel': 'Test'})
    
    def test_call_tracking_and_reset(self):
        """Test call tracking and reset functionality."""
        mock = MockSummaryWriter()
        
        # Make several calls
        video_metadata = {'title': 'Test', 'channel': 'Test'}
        mock.generate_summary("https://youtu.be/test1", video_metadata)
        mock.generate_summary("https://youtu.be/test2", video_metadata)
        mock.validate_configuration()
        
        # Verify tracking
        assert len(mock.generate_summary_calls) == 2
        assert len(mock.validate_configuration_calls) == 1
        
        # Reset and verify
        mock.reset_calls()
        assert len(mock.generate_summary_calls) == 0
        assert len(mock.validate_configuration_calls) == 0
    
    def test_dynamic_configuration(self):
        """Test dynamic configuration changes."""
        mock = MockSummaryWriter()
        
        # Add response for URL
        test_url = "https://youtu.be/dynamic123"
        custom_response = "Dynamic response"
        mock.set_response_for_url(test_url, custom_response)
        
        video_metadata = {'title': 'Test', 'channel': 'Test'}
        summary = mock.generate_summary(test_url, video_metadata)
        assert summary == custom_response
        
        # Add failure for URL
        mock.set_failure_for_url(test_url)
        with pytest.raises(SummaryGenerationError):
            mock.generate_summary(test_url, video_metadata)
        
        # Clear failures
        mock.clear_failures()
        summary = mock.generate_summary(test_url, video_metadata)
        assert summary == custom_response  # Should work again


class TestMockStorage:
    """Test the MockStorage implementation."""
    
    def test_successful_storage(self):
        """Test successful video data storage."""
        mock = MockStorage()
        
        video_data = {
            'Title': 'Test Video',
            'Channel': 'Test Channel',
            'Video URL': 'https://youtu.be/test123',
            'Cover': 'https://img.youtube.com/vi/test123/maxresdefault.jpg',
            'Summary': 'Test summary content'
        }
        
        result = mock.store_video_summary(video_data)
        assert result is True
        
        # Verify storage
        assert len(mock.stored_videos) == 1
        stored_video = mock.stored_videos[0]
        assert stored_video['Title'] == 'Test Video'
        assert stored_video['Channel'] == 'Test Channel'
        
        # Verify call tracking
        assert len(mock.store_video_summary_calls) == 1
        assert mock.store_video_summary_calls[0] == video_data
    
    def test_failure_simulation(self):
        """Test failure simulation for error handling tests."""
        mock = MockStorage(should_fail=True)
        
        video_data = {'Title': 'Test Video'}
        
        with pytest.raises(StorageError) as exc_info:
            mock.store_video_summary(video_data)
        
        assert "Mock storage failed" in str(exc_info.value)
        
        # Verify call was still tracked
        assert len(mock.store_video_summary_calls) == 1
        # But video was not stored
        assert len(mock.stored_videos) == 0
    
    def test_title_specific_failures(self):
        """Test title-specific failure configuration."""
        fail_title = "Failing Video"
        mock = MockStorage(fail_on_titles=[fail_title])
        
        # Should fail for specific title
        with pytest.raises(StorageError):
            mock.store_video_summary({'Title': fail_title})
        
        # Should succeed for other titles
        result = mock.store_video_summary({'Title': 'Success Video'})
        assert result is True
        assert len(mock.stored_videos) == 1
    
    def test_configuration_validation(self):
        """Test configuration validation behavior."""
        # Valid configuration
        mock = MockStorage(configuration_valid=True)
        assert mock.validate_configuration() is True
        assert len(mock.validate_configuration_calls) == 1
        
        # Invalid configuration
        mock = MockStorage(configuration_valid=False)
        assert mock.validate_configuration() is False
        
        # Should raise error during storage
        with pytest.raises(ConfigurationError):
            mock.store_video_summary({'Title': 'Test'})
    
    def test_target_location_finding(self):
        """Test target location finding functionality."""
        target_id = "test-database-123"
        mock = MockStorage(target_location=target_id)
        
        location = mock.find_target_location()
        assert location == target_id
        assert len(mock.find_target_location_calls) == 1
        
        # Test with no target location
        mock = MockStorage(target_location=None)
        location = mock.find_target_location()
        assert location is None
    
    def test_target_location_with_invalid_config(self):
        """Test target location finding with invalid configuration."""
        mock = MockStorage(configuration_valid=False)
        
        with pytest.raises(ConfigurationError):
            mock.find_target_location()
    
    def test_storage_retrieval_helpers(self):
        """Test helper methods for retrieving stored data."""
        mock = MockStorage()
        
        # Store multiple videos
        video1 = {'Title': 'Video One', 'Channel': 'Channel A'}
        video2 = {'Title': 'Video Two', 'Channel': 'Channel B'}
        
        mock.store_video_summary(video1)
        mock.store_video_summary(video2)
        
        # Test retrieval by title
        retrieved = mock.get_stored_video_by_title('Video One')
        assert retrieved is not None
        assert retrieved['Channel'] == 'Channel A'
        
        # Test non-existent title
        retrieved = mock.get_stored_video_by_title('Non-existent')
        assert retrieved is None
    
    def test_call_tracking_and_reset(self):
        """Test call tracking and reset functionality."""
        mock = MockStorage()
        
        # Make several calls
        mock.store_video_summary({'Title': 'Test1'})
        mock.store_video_summary({'Title': 'Test2'})
        mock.validate_configuration()
        mock.find_target_location()
        
        # Verify tracking
        assert len(mock.store_video_summary_calls) == 2
        assert len(mock.validate_configuration_calls) == 1
        assert len(mock.find_target_location_calls) == 1
        assert len(mock.stored_videos) == 2
        
        # Reset calls but keep storage
        mock.reset_calls()
        assert len(mock.store_video_summary_calls) == 0
        assert len(mock.validate_configuration_calls) == 0
        assert len(mock.find_target_location_calls) == 0
        assert len(mock.stored_videos) == 2  # Storage preserved
        
        # Clear storage
        mock.clear_storage()
        assert len(mock.stored_videos) == 0
    
    def test_dynamic_configuration(self):
        """Test dynamic configuration changes."""
        mock = MockStorage()
        
        # Add failure for title
        test_title = "Dynamic Test"
        mock.set_failure_for_title(test_title)
        
        with pytest.raises(StorageError):
            mock.store_video_summary({'Title': test_title})
        
        # Clear failures
        mock.clear_failures()
        result = mock.store_video_summary({'Title': test_title})
        assert result is True


class TestMockMetadataExtractor:
    """Test the MockMetadataExtractor implementation."""
    
    def test_url_validation(self):
        """Test URL validation functionality."""
        mock = MockMetadataExtractor()
        
        # Valid URLs
        assert mock.validate_url("https://youtube.com/watch?v=test123") is True
        assert mock.validate_url("https://youtu.be/test123") is True
        assert mock.validate_url("https://www.youtube.com/watch?v=test123") is True
        
        # Invalid URLs
        assert mock.validate_url("https://vimeo.com/123456") is False
        assert mock.validate_url("not a url") is False
        assert mock.validate_url("") is False
        assert mock.validate_url(None) is False
        
        # Verify call tracking
        assert len(mock.validate_url_calls) == 7
    
    def test_video_id_extraction(self):
        """Test video ID extraction from URLs."""
        mock = MockMetadataExtractor()
        
        # Test watch URL
        video_id = mock.extract_video_id("https://youtube.com/watch?v=abcdef12345")
        assert video_id == "abcdef12345"
        
        # Test short URL
        video_id = mock.extract_video_id("https://youtu.be/xyz789")
        assert video_id == "xyz789"
        
        # Test with parameters
        video_id = mock.extract_video_id("https://youtube.com/watch?v=test123&t=30s")
        assert video_id == "test123"
        
        # Verify call tracking
        assert len(mock.extract_video_id_calls) == 3
    
    def test_video_id_extraction_invalid_url(self):
        """Test video ID extraction with invalid URLs."""
        mock = MockMetadataExtractor(invalid_urls=["https://invalid.com/video"])
        
        with pytest.raises(InvalidURLError):
            mock.extract_video_id("https://invalid.com/video")
    
    def test_successful_metadata_extraction(self):
        """Test successful metadata extraction."""
        mock = MockMetadataExtractor()
        
        video_url = "https://youtu.be/test123"
        metadata = mock.extract_metadata(video_url)
        
        # Verify default metadata structure
        assert 'title' in metadata
        assert 'channel' in metadata
        assert 'description' in metadata
        assert 'published_at' in metadata
        assert 'thumbnail_url' in metadata
        assert 'video_id' in metadata
        
        # Verify video ID is extracted correctly
        assert metadata['video_id'] == 'test123'
        assert 'test123' in metadata['thumbnail_url']
        
        # Verify call tracking
        assert len(mock.extract_metadata_calls) == 1
        assert mock.extract_metadata_calls[0] == video_url
    
    def test_custom_metadata_responses(self):
        """Test custom metadata configuration for specific URLs."""
        custom_metadata = {
            'title': 'Custom Video Title',
            'channel': 'Custom Channel',
            'description': 'Custom description',
            'published_at': '2024-02-01T10:00:00Z',
            'thumbnail_url': 'https://custom.thumbnail.url/image.jpg'
        }
        
        test_url = "https://youtu.be/custom123"
        mock = MockMetadataExtractor(metadata_responses={
            test_url: custom_metadata
        })
        
        metadata = mock.extract_metadata(test_url)
        
        # Verify custom metadata is returned
        assert metadata['title'] == 'Custom Video Title'
        assert metadata['channel'] == 'Custom Channel'
        assert metadata['description'] == 'Custom description'
        assert metadata['video_id'] == 'custom123'  # Should be added automatically
    
    def test_failure_simulation(self):
        """Test failure simulation for error handling tests."""
        mock = MockMetadataExtractor(should_fail=True)
        
        with pytest.raises(MetadataExtractionError) as exc_info:
            mock.extract_metadata("https://youtu.be/test123")
        
        assert "Mock metadata extraction failed" in str(exc_info.value)
        
        # Verify call was still tracked
        assert len(mock.extract_metadata_calls) == 1
    
    def test_url_specific_failures(self):
        """Test URL-specific failure configuration."""
        fail_url = "https://youtu.be/fail123"
        mock = MockMetadataExtractor(fail_on_urls=[fail_url])
        
        # Should fail for specific URL
        with pytest.raises(MetadataExtractionError):
            mock.extract_metadata(fail_url)
        
        # Should succeed for other URLs
        metadata = mock.extract_metadata("https://youtu.be/success123")
        assert metadata['video_id'] == 'success123'
    
    def test_invalid_url_handling(self):
        """Test handling of invalid URLs."""
        invalid_url = "https://not-youtube.com/video"
        mock = MockMetadataExtractor(invalid_urls=[invalid_url])
        
        # Should fail validation
        assert mock.validate_url(invalid_url) is False
        
        # Should raise error during extraction
        with pytest.raises(InvalidURLError):
            mock.extract_metadata(invalid_url)
    
    def test_call_tracking_and_reset(self):
        """Test call tracking and reset functionality."""
        mock = MockMetadataExtractor()
        
        # Make several calls
        mock.validate_url("https://youtu.be/test1")
        mock.extract_video_id("https://youtu.be/test2")
        mock.extract_metadata("https://youtu.be/test3")
        
        # Verify tracking
        # Call pattern:
        # 1. Direct validate_url call
        # 2. extract_video_id calls validate_url internally
        # 3. extract_metadata calls validate_url and extract_video_id (which also calls validate_url)
        assert len(mock.validate_url_calls) == 4  # 1 direct + 1 from extract_video_id + 2 from extract_metadata
        assert len(mock.extract_video_id_calls) == 2  # 1 direct + 1 from extract_metadata
        assert len(mock.extract_metadata_calls) == 1
        
        # Reset and verify
        mock.reset_calls()
        assert len(mock.validate_url_calls) == 0
        assert len(mock.extract_video_id_calls) == 0
        assert len(mock.extract_metadata_calls) == 0
    
    def test_dynamic_configuration(self):
        """Test dynamic configuration changes."""
        mock = MockMetadataExtractor()
        
        # Add custom metadata for URL
        test_url = "https://youtu.be/dynamic123"
        custom_metadata = {'title': 'Dynamic Title', 'channel': 'Dynamic Channel'}
        mock.set_metadata_for_url(test_url, custom_metadata)
        
        metadata = mock.extract_metadata(test_url)
        assert metadata['title'] == 'Dynamic Title'
        
        # Add failure for URL
        mock.set_failure_for_url(test_url)
        with pytest.raises(MetadataExtractionError):
            mock.extract_metadata(test_url)
        
        # Add invalid URL
        mock.set_invalid_url(test_url)
        assert mock.validate_url(test_url) is False
        
        # Clear failures (this should clear invalid_urls too)
        mock.clear_failures()
        # Should now be valid again since invalid_urls was cleared
        assert mock.validate_url(test_url) is True


class TestMockFactoryFunctions:
    """Test the convenience factory functions."""
    
    def test_create_successful_mocks(self):
        """Test creation of successful mock set."""
        extractor, writer, storage = create_successful_mocks()
        
        # Test that all mocks are properly configured for success
        assert extractor.validate_url("https://youtu.be/test123") is True
        assert writer.validate_configuration() is True
        assert storage.validate_configuration() is True
        
        # Test basic operations work
        metadata = extractor.extract_metadata("https://youtu.be/test123")
        assert metadata['video_id'] == 'test123'
        
        summary = writer.generate_summary("https://youtu.be/test123", metadata)
        assert "MockSummaryWriter" in summary
        
        video_data = {'Title': 'Test', 'Summary': summary}
        result = storage.store_video_summary(video_data)
        assert result is True
    
    def test_create_failing_mocks(self):
        """Test creation of failing mock set."""
        extractor, writer, storage = create_failing_mocks()
        
        # Test that all mocks are configured to fail
        with pytest.raises(MetadataExtractionError):
            extractor.extract_metadata("https://youtu.be/test123")
        
        with pytest.raises(SummaryGenerationError):
            writer.generate_summary("https://youtu.be/test123", {})
        
        with pytest.raises(StorageError):
            storage.store_video_summary({'Title': 'Test'})
    
    def test_create_mixed_mocks(self):
        """Test creation of mixed success/failure mock set."""
        extractor, writer, storage = create_mixed_mocks()
        
        # Test successful operations
        metadata = extractor.extract_metadata("https://youtu.be/success123")
        assert metadata['video_id'] == 'success123'
        
        summary = writer.generate_summary("https://youtu.be/success123", metadata)
        assert "MockSummaryWriter" in summary
        
        result = storage.store_video_summary({'Title': 'Success Video', 'Summary': summary})
        assert result is True
        
        # Test configured failures
        with pytest.raises(MetadataExtractionError):
            extractor.extract_metadata("https://youtu.be/fail_video")
        
        with pytest.raises(SummaryGenerationError):
            writer.generate_summary("https://youtu.be/summary_fail", metadata)
        
        with pytest.raises(StorageError):
            storage.store_video_summary({'Title': 'Failing Video Title'})
        
        # Test invalid URL
        assert extractor.validate_url("https://not-youtube.com/video") is False


class TestMockIntegration:
    """Test integration scenarios using mocks."""
    
    def test_complete_workflow_simulation(self):
        """Test simulating a complete video processing workflow."""
        # Create mocks with specific configurations
        extractor = MockMetadataExtractor()
        writer = MockSummaryWriter()
        storage = MockStorage()
        
        # Configure custom responses
        test_url = "https://youtu.be/workflow123"
        custom_metadata = {
            'title': 'Workflow Test Video',
            'channel': 'Test Channel',
            'description': 'Test workflow description'
        }
        extractor.set_metadata_for_url(test_url, custom_metadata)
        
        custom_summary = "# Workflow Test Summary\n\nThis is a test workflow summary."
        writer.set_response_for_url(test_url, custom_summary)
        
        # Simulate complete workflow
        # Step 1: Extract metadata
        metadata = extractor.extract_metadata(test_url)
        assert metadata['title'] == 'Workflow Test Video'
        
        # Step 2: Generate summary
        summary = writer.generate_summary(test_url, metadata)
        assert summary == custom_summary
        
        # Step 3: Store results
        video_data = {
            'Title': metadata['title'],
            'Channel': metadata['channel'],
            'Video URL': test_url,
            'Summary': summary
        }
        result = storage.store_video_summary(video_data)
        assert result is True
        
        # Verify all operations were tracked
        assert len(extractor.extract_metadata_calls) == 1
        assert len(writer.generate_summary_calls) == 1
        assert len(storage.store_video_summary_calls) == 1
        
        # Verify stored data
        stored_video = storage.get_stored_video_by_title('Workflow Test Video')
        assert stored_video is not None
        assert stored_video['Summary'] == custom_summary
    
    def test_error_propagation_simulation(self):
        """Test simulating error propagation through workflow."""
        # Create mocks with different failure points
        extractor = MockMetadataExtractor(fail_on_urls=["https://youtu.be/extract_fail"])
        writer = MockSummaryWriter(fail_on_urls=["https://youtu.be/summary_fail"])
        storage = MockStorage(fail_on_titles=["Storage Fail Video"])
        
        # Test metadata extraction failure
        with pytest.raises(MetadataExtractionError):
            extractor.extract_metadata("https://youtu.be/extract_fail")
        
        # Test summary generation failure
        metadata = extractor.extract_metadata("https://youtu.be/summary_fail")
        with pytest.raises(SummaryGenerationError):
            writer.generate_summary("https://youtu.be/summary_fail", metadata)
        
        # Test storage failure
        success_url = "https://youtu.be/success123"
        metadata = extractor.extract_metadata(success_url)
        summary = writer.generate_summary(success_url, metadata)
        
        video_data = {
            'Title': 'Storage Fail Video',
            'Summary': summary
        }
        with pytest.raises(StorageError):
            storage.store_video_summary(video_data)
        
        # Verify partial operations were still tracked
        assert len(extractor.extract_metadata_calls) == 3  # All attempts tracked
        assert len(writer.generate_summary_calls) == 2  # Two successful calls
        assert len(storage.store_video_summary_calls) == 1  # One attempt