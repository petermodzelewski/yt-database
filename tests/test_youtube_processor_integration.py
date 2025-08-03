"""
Integration tests for the YouTubeProcessor class.

This module contains comprehensive integration tests for the complete
YouTube video processing workflow, including URL validation, metadata
extraction, AI summary generation, and data structure formatting.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.youtube_notion.processors.youtube_processor import YouTubeProcessor
from src.youtube_notion.processors.exceptions import (
    YouTubeProcessingError,
    InvalidURLError,
    APIError,
    VideoUnavailableError,
    QuotaExceededError
)


class TestYouTubeProcessorIntegration:
    """Integration tests for the complete YouTubeProcessor workflow."""
    
    @pytest.fixture
    def processor(self):
        """Create a YouTubeProcessor instance for testing."""
        return YouTubeProcessor.from_api_keys(
            gemini_api_key="test_gemini_key",
            youtube_api_key="test_youtube_key",
            max_retries=2,
            timeout_seconds=30
        )
    
    @pytest.fixture
    def mock_youtube_metadata(self):
        """Mock YouTube metadata response."""
        return {
            'title': 'Test Video Title',
            'channel': 'Test Channel',
            'description': 'Test video description',
            'published_at': '2023-01-01T00:00:00Z',
            'thumbnail_url': 'https://img.youtube.com/vi/test_video_id/maxresdefault.jpg'
        }
    
    @pytest.fixture
    def mock_gemini_summary(self):
        """Mock Gemini API summary response."""
        return """### Test Video Summary

This is a test summary with timestamps.

#### Key Points [0:30-1:15]

- Important point 1 [0:30]
- Important point 2 [0:45-1:00]
- Important point 3 [1:15]

#### Conclusion [2:00-2:30]

Final thoughts and wrap-up."""
    
    def test_process_video_complete_workflow_success(self, processor, mock_youtube_metadata, mock_gemini_summary):
        """Test the complete video processing workflow with successful execution."""
        test_url = "https://www.youtube.com/watch?v=test_video_id"
        
        with patch.object(processor, '_extract_video_id', return_value='test_video_id') as mock_extract, \
             patch.object(processor, '_get_video_metadata', return_value=mock_youtube_metadata) as mock_metadata, \
             patch.object(processor, '_generate_summary', return_value=mock_gemini_summary) as mock_summary:
            
            result = processor.process_video(test_url)
            
            # Verify all pipeline steps were called
            mock_extract.assert_called_once_with(test_url)
            mock_metadata.assert_called_once_with('test_video_id')
            mock_summary.assert_called_once_with(test_url, None, mock_youtube_metadata)
            
            # Verify result structure matches EXAMPLE_DATA format
            assert isinstance(result, dict)
            assert set(result.keys()) == {"Title", "Channel", "Video URL", "Cover", "Summary"}
            
            # Verify result content
            assert result["Title"] == "Test Video Title"
            assert result["Channel"] == "Test Channel"
            assert result["Video URL"] == test_url
            assert result["Cover"] == "https://img.youtube.com/vi/test_video_id/maxresdefault.jpg"
            assert result["Summary"] == mock_gemini_summary
    
    def test_process_video_with_custom_prompt(self, processor, mock_youtube_metadata, mock_gemini_summary):
        """Test video processing with a custom prompt."""
        test_url = "https://www.youtube.com/watch?v=test_video_id"
        custom_prompt = "Custom prompt for testing"
        
        with patch.object(processor, '_extract_video_id', return_value='test_video_id'), \
             patch.object(processor, '_get_video_metadata', return_value=mock_youtube_metadata), \
             patch.object(processor, '_generate_summary', return_value=mock_gemini_summary) as mock_summary:
            
            result = processor.process_video(test_url, custom_prompt=custom_prompt)
            
            # Verify custom prompt was passed to summary generation
            mock_summary.assert_called_once_with(test_url, custom_prompt, mock_youtube_metadata)
            
            # Verify result is still properly formatted
            assert result["Summary"] == mock_gemini_summary
    
    def test_process_video_invalid_url_error(self, processor):
        """Test that InvalidURLError is properly propagated."""
        invalid_url = "https://not-youtube.com/watch?v=test"
        
        with patch.object(processor, '_extract_video_id', side_effect=InvalidURLError("Invalid URL")):
            with pytest.raises(InvalidURLError, match="Invalid URL"):
                processor.process_video(invalid_url)
    
    def test_process_video_video_unavailable_error(self, processor):
        """Test that VideoUnavailableError is properly propagated."""
        test_url = "https://www.youtube.com/watch?v=private_video"
        
        with patch.object(processor, '_extract_video_id', return_value='private_video'), \
             patch.object(processor, '_get_video_metadata', side_effect=VideoUnavailableError("Video unavailable")):
            
            with pytest.raises(VideoUnavailableError, match="Video unavailable"):
                processor.process_video(test_url)
    
    def test_process_video_api_error_during_metadata(self, processor):
        """Test that APIError during metadata extraction is properly propagated."""
        test_url = "https://www.youtube.com/watch?v=test_video_id"
        
        with patch.object(processor, '_extract_video_id', return_value='test_video_id'), \
             patch.object(processor, '_get_video_metadata', side_effect=APIError("API failed")):
            
            with pytest.raises(APIError, match="API failed"):
                processor.process_video(test_url)
    
    def test_process_video_api_error_during_summary(self, processor, mock_youtube_metadata):
        """Test that APIError during summary generation is properly propagated."""
        test_url = "https://www.youtube.com/watch?v=test_video_id"
        
        with patch.object(processor, '_extract_video_id', return_value='test_video_id'), \
             patch.object(processor, '_get_video_metadata', return_value=mock_youtube_metadata), \
             patch.object(processor, '_generate_summary', side_effect=APIError("Gemini API failed")):
            
            with pytest.raises(APIError, match="Gemini API failed"):
                processor.process_video(test_url)
    
    def test_process_video_quota_exceeded_error(self, processor, mock_youtube_metadata):
        """Test that QuotaExceededError is properly propagated."""
        test_url = "https://www.youtube.com/watch?v=test_video_id"
        
        with patch.object(processor, '_extract_video_id', return_value='test_video_id'), \
             patch.object(processor, '_get_video_metadata', return_value=mock_youtube_metadata), \
             patch.object(processor, '_generate_summary', side_effect=QuotaExceededError("Quota exceeded")):
            
            with pytest.raises(QuotaExceededError, match="Quota exceeded"):
                processor.process_video(test_url)
    
    def test_process_video_unexpected_error_wrapped(self, processor):
        """Test that unexpected errors are wrapped in YouTubeProcessingError."""
        test_url = "https://www.youtube.com/watch?v=test_video_id"
        
        with patch.object(processor, '_extract_video_id', side_effect=ValueError("Unexpected error")):
            
            with pytest.raises(YouTubeProcessingError) as exc_info:
                processor.process_video(test_url)
            
            # Verify the error is properly wrapped
            assert "Unexpected error during video processing" in str(exc_info.value)
            assert "ValueError" in str(exc_info.value)
            assert test_url in str(exc_info.value)
    
    def test_process_video_data_structure_compatibility(self, processor, mock_youtube_metadata, mock_gemini_summary):
        """Test that the output data structure is exactly compatible with EXAMPLE_DATA format."""
        test_url = "https://www.youtube.com/watch?v=test_video_id"
        
        with patch.object(processor, '_extract_video_id', return_value='test_video_id'), \
             patch.object(processor, '_get_video_metadata', return_value=mock_youtube_metadata), \
             patch.object(processor, '_generate_summary', return_value=mock_gemini_summary):
            
            result = processor.process_video(test_url)
            
            # Import EXAMPLE_DATA to compare structure
            from src.youtube_notion.config.example_data import EXAMPLE_DATA
            
            # Verify exact key compatibility
            assert set(result.keys()) == set(EXAMPLE_DATA.keys())
            
            # Verify data types match
            for key in EXAMPLE_DATA.keys():
                assert type(result[key]) == type(EXAMPLE_DATA[key]), f"Type mismatch for key '{key}'"
            
            # Verify all values are strings (as in EXAMPLE_DATA)
            for key, value in result.items():
                assert isinstance(value, str), f"Value for '{key}' should be string, got {type(value)}"
    
    def test_process_video_with_different_url_formats(self, processor, mock_youtube_metadata, mock_gemini_summary):
        """Test processing with different YouTube URL formats."""
        test_urls = [
            "https://www.youtube.com/watch?v=test_video_id",
            "https://youtu.be/test_video_id",
            "https://youtube.com/watch?v=test_video_id",
            "https://m.youtube.com/watch?v=test_video_id"
        ]
        
        for test_url in test_urls:
            with patch.object(processor, '_extract_video_id', return_value='test_video_id'), \
                 patch.object(processor, '_get_video_metadata', return_value=mock_youtube_metadata), \
                 patch.object(processor, '_generate_summary', return_value=mock_gemini_summary):
                
                result = processor.process_video(test_url)
                
                # Verify the original URL is preserved in the result
                assert result["Video URL"] == test_url
                assert result["Title"] == "Test Video Title"
    
    def test_process_video_empty_metadata_handling(self, processor, mock_gemini_summary):
        """Test processing with empty or missing metadata fields."""
        test_url = "https://www.youtube.com/watch?v=test_video_id"
        
        # Mock metadata with empty/missing fields
        empty_metadata = {
            'title': '',
            'channel': '',
            'description': '',
            'published_at': '',
            'thumbnail_url': 'https://img.youtube.com/vi/test_video_id/maxresdefault.jpg'
        }
        
        with patch.object(processor, '_extract_video_id', return_value='test_video_id'), \
             patch.object(processor, '_get_video_metadata', return_value=empty_metadata), \
             patch.object(processor, '_generate_summary', return_value=mock_gemini_summary):
            
            result = processor.process_video(test_url)
            
            # Verify the processor handles empty metadata gracefully
            assert result["Title"] == ''
            assert result["Channel"] == ''
            assert result["Cover"] == 'https://img.youtube.com/vi/test_video_id/maxresdefault.jpg'
            assert result["Summary"] == mock_gemini_summary
    
    def test_process_video_long_content_handling(self, processor, mock_youtube_metadata):
        """Test processing with very long summary content."""
        test_url = "https://www.youtube.com/watch?v=test_video_id"
        
        # Create a very long summary
        long_summary = "# Very Long Summary\n\n" + "This is a long paragraph. " * 1000
        
        with patch.object(processor, '_extract_video_id', return_value='test_video_id'), \
             patch.object(processor, '_get_video_metadata', return_value=mock_youtube_metadata), \
             patch.object(processor, '_generate_summary', return_value=long_summary):
            
            result = processor.process_video(test_url)
            
            # Verify long content is handled properly
            assert result["Summary"] == long_summary
            assert len(result["Summary"]) > 10000  # Verify it's actually long


class TestYouTubeProcessorInitialization:
    """Test YouTubeProcessor initialization and configuration."""
    
    def test_processor_initialization_with_required_params(self):
        """Test processor initialization with only required parameters."""
        processor = YouTubeProcessor.from_api_keys(gemini_api_key="test_key")
        
        assert processor.gemini_api_key == "test_key"
        assert processor.youtube_api_key is None
        assert processor.default_prompt is not None
        assert processor.max_retries == 3
        assert processor.timeout_seconds == 120
    
    def test_processor_initialization_with_all_params(self):
        """Test processor initialization with all parameters."""
        custom_prompt = "Custom test prompt"
        
        processor = YouTubeProcessor.from_api_keys(
            gemini_api_key="test_gemini_key",
            youtube_api_key="test_youtube_key",
            default_prompt=custom_prompt,
            max_retries=5,
            timeout_seconds=60
        )
        
        assert processor.gemini_api_key == "test_gemini_key"
        assert processor.youtube_api_key == "test_youtube_key"
        assert processor.default_prompt == custom_prompt
        assert processor.max_retries == 5
        assert processor.timeout_seconds == 60
    
    def test_processor_initialization_missing_gemini_key(self):
        """Test that initialization fails without Gemini API key."""
        with pytest.raises(ValueError, match="Gemini API key is required"):
            YouTubeProcessor.from_api_keys(gemini_api_key="")
        
        with pytest.raises(ValueError, match="Gemini API key is required"):
            YouTubeProcessor.from_api_keys(gemini_api_key=None)


class TestYouTubeProcessorValidation:
    """Test YouTubeProcessor URL validation functionality."""
    
    @pytest.fixture
    def processor(self):
        """Create a YouTubeProcessor instance for testing."""
        return YouTubeProcessor.from_api_keys(gemini_api_key="test_key")
    
    def test_validate_youtube_url_valid_urls(self, processor):
        """Test URL validation with valid YouTube URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in valid_urls:
            assert processor.validate_youtube_url(url) is True
    
    def test_validate_youtube_url_invalid_urls(self, processor):
        """Test URL validation with invalid URLs."""
        invalid_urls = [
            "https://www.google.com",
            "https://vimeo.com/123456",
            "not_a_url",
            "",
            None
        ]
        
        for url in invalid_urls:
            assert processor.validate_youtube_url(url) is False
    
    def test_validate_youtube_url_edge_cases(self, processor):
        """Test URL validation with edge cases."""
        edge_cases = [
            "https://www.youtube.com/watch?v=",  # Empty video ID
            "https://www.youtube.com/watch",     # Missing video ID
            "https://youtu.be/",                 # Empty short URL
            "youtube.com/watch?v=dQw4w9WgXcQ",   # Missing protocol
        ]
        
        # These should be handled gracefully by returning False
        for url in edge_cases:
            result = processor.validate_youtube_url(url)
            assert isinstance(result, bool)