"""
Unit tests for VideoMetadataExtractor.

This module contains comprehensive tests for the VideoMetadataExtractor class,
including URL validation, video ID extraction, and metadata retrieval with
both API and web scraping approaches.
"""

import pytest
import requests
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from googleapiclient.errors import HttpError
from src.youtube_notion.extractors.video_metadata_extractor import VideoMetadataExtractor
from src.youtube_notion.utils.exceptions import (
    InvalidURLError,
    APIError,
    VideoUnavailableError,
    QuotaExceededError,
    MetadataExtractionError
)


class TestVideoMetadataExtractor:
    """Test cases for VideoMetadataExtractor class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = VideoMetadataExtractor()
        self.extractor_with_api = VideoMetadataExtractor(youtube_api_key="test_api_key")
    
    def test_init_without_api_key(self):
        """Test initialization without API key."""
        extractor = VideoMetadataExtractor()
        assert extractor.youtube_api_key is None
        assert extractor.timeout_seconds == 10
    
    def test_init_with_api_key(self):
        """Test initialization with API key."""
        extractor = VideoMetadataExtractor(youtube_api_key="test_key", timeout_seconds=30)
        assert extractor.youtube_api_key == "test_key"
        assert extractor.timeout_seconds == 30
    
    # URL Validation Tests
    
    def test_validate_url_valid_youtube_urls(self):
        """Test URL validation with valid YouTube URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=123s",
            "www.youtube.com/watch?v=dQw4w9WgXcQ",  # Without protocol
            "youtube.com/watch?v=dQw4w9WgXcQ",     # Without www and protocol
        ]
        
        for url in valid_urls:
            assert self.extractor.validate_url(url), f"URL should be valid: {url}"
    
    def test_validate_url_invalid_urls(self):
        """Test URL validation with invalid URLs."""
        invalid_urls = [
            "",
            None,
            "not_a_url",
            "https://example.com",
            "https://vimeo.com/123456",
            "https://www.youtube.com/watch",  # Missing video ID
            "https://www.youtube.com/watch?v=",  # Empty video ID
            "https://www.youtube.com/watch?v=invalid_id",  # Invalid video ID format
        ]
        
        for url in invalid_urls:
            assert not self.extractor.validate_url(url), f"URL should be invalid: {url}"
    
    # Video ID Extraction Tests
    
    def test_extract_video_id_standard_urls(self):
        """Test video ID extraction from standard YouTube URLs."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/v/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            result = self.extractor.extract_video_id(url)
            assert result == expected_id, f"Expected {expected_id}, got {result} for URL: {url}"
    
    def test_extract_video_id_with_parameters(self):
        """Test video ID extraction from URLs with additional parameters."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=123s", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLxyz", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ?t=123", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            result = self.extractor.extract_video_id(url)
            assert result == expected_id, f"Expected {expected_id}, got {result} for URL: {url}"
    
    def test_extract_video_id_without_protocol(self):
        """Test video ID extraction from URLs without protocol."""
        test_cases = [
            ("www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            result = self.extractor.extract_video_id(url)
            assert result == expected_id, f"Expected {expected_id}, got {result} for URL: {url}"
    
    def test_extract_video_id_invalid_inputs(self):
        """Test video ID extraction with invalid inputs."""
        invalid_inputs = [
            ("", "URL must be a non-empty string"),
            (None, "URL must be a non-empty string"),
            (123, "URL must be a non-empty string"),
            ("not_a_url", "URL is not from a supported YouTube domain"),
            ("https://example.com", "URL is not from a supported YouTube domain"),
            ("https://www.youtube.com/watch", "Could not extract video ID from URL"),
            ("https://www.youtube.com/watch?v=", "Could not extract video ID from URL"),
            ("https://www.youtube.com/watch?v=invalid", "Extracted video ID has invalid format"),
        ]
        
        for invalid_input, expected_error in invalid_inputs:
            with pytest.raises(InvalidURLError) as exc_info:
                self.extractor.extract_video_id(invalid_input)
            assert expected_error in str(exc_info.value)
    
    def test_is_valid_video_id(self):
        """Test video ID format validation."""
        valid_ids = [
            "dQw4w9WgXcQ",  # Standard format
            "abcdefghijk",  # All lowercase
            "ABCDEFGHIJK",  # All uppercase
            "123456789ab",  # With numbers
            "abc-def_hij",  # With hyphens and underscores
        ]
        
        for video_id in valid_ids:
            assert self.extractor._is_valid_video_id(video_id), f"Video ID should be valid: {video_id}"
        
        invalid_ids = [
            "",              # Empty
            None,            # None
            "short",         # Too short
            "toolongvideoid", # Too long
            "invalid@id",    # Invalid characters
            "invalid id",    # Space
        ]
        
        for video_id in invalid_ids:
            assert not self.extractor._is_valid_video_id(video_id), f"Video ID should be invalid: {video_id}"
    
    # Metadata Extraction Tests
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.build')
    def test_extract_metadata_via_api_success(self, mock_build):
        """Test successful metadata extraction via YouTube API."""
        # Mock API response
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube
        
        mock_request = Mock()
        mock_youtube.videos.return_value.list.return_value = mock_request
        
        mock_response = {
            'items': [{
                'snippet': {
                    'title': 'Test Video Title',
                    'channelTitle': 'Test Channel',
                    'description': 'Test description',
                    'publishedAt': '2023-01-01T00:00:00Z'
                },
                'contentDetails': {
                    'duration': 'PT1H2M3S'
                }
            }]
        }
        mock_request.execute.return_value = mock_response
        
        # Test extraction
        result = self.extractor_with_api.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        expected = {
            'title': 'Test Video Title',
            'channel': 'Test Channel',
            'description': 'Test description',
            'published_at': '2023-01-01T00:00:00Z',
            'thumbnail_url': 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
            'video_id': 'dQw4w9WgXcQ',
            'duration': 3723
        }
        
        assert result == expected
        mock_build.assert_called_once_with('youtube', 'v3', developerKey='test_api_key')
        mock_youtube.videos.return_value.list.assert_called_once_with(
            part='snippet,contentDetails',
            id='dQw4w9WgXcQ'
        )
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.build')
    def test_extract_metadata_via_api_video_not_found(self, mock_build):
        """Test API extraction when video is not found."""
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube
        
        mock_request = Mock()
        mock_youtube.videos.return_value.list.return_value = mock_request
        mock_request.execute.return_value = {'items': []}
        
        with pytest.raises(VideoUnavailableError) as exc_info:
            self.extractor_with_api.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        assert "Video not found or is not accessible" in str(exc_info.value)
        assert exc_info.value.video_id == "dQw4w9WgXcQ"
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.build')
    def test_extract_metadata_via_api_quota_exceeded(self, mock_build):
        """Test API extraction when quota is exceeded."""
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube
        
        mock_request = Mock()
        mock_youtube.videos.return_value.list.return_value = mock_request
        
        # Mock HttpError for quota exceeded
        mock_response = Mock()
        mock_response.status = 403
        error_details = [{'reason': 'quotaExceeded', 'message': 'Quota exceeded'}]
        http_error = HttpError(mock_response, b'quota exceeded')
        http_error.error_details = error_details
        mock_request.execute.side_effect = http_error
        
        with pytest.raises(QuotaExceededError) as exc_info:
            self.extractor_with_api.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        assert "YouTube API quota exceeded" in str(exc_info.value)
        assert exc_info.value.api_name == "YouTube Data API"
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.build')
    def test_extract_metadata_via_api_authentication_error(self, mock_build):
        """Test API extraction with authentication error."""
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube
        
        mock_request = Mock()
        mock_youtube.videos.return_value.list.return_value = mock_request
        
        # Mock HttpError for authentication failure
        mock_response = Mock()
        mock_response.status = 401
        http_error = HttpError(mock_response, b'unauthorized')
        http_error.error_details = [{'message': 'Invalid API key'}]
        mock_request.execute.side_effect = http_error
        
        # Mock web scraping fallback to succeed
        with patch('requests.get') as mock_get:
            mock_scraping_response = Mock()
            mock_scraping_response.text = '''
            <html>
            <script>
            var ytInitialData = {"contents":{"videoDetails":{"title":"Test Video","author":"Test Channel"}}};
            </script>
            </html>
            '''
            mock_get.return_value = mock_scraping_response
            
            # Should fall back to web scraping instead of raising error
            result = self.extractor_with_api.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            
            # Verify that web scraping was used as fallback
            assert result is not None
            assert 'title' in result
    
    @patch('requests.get')
    def test_extract_metadata_via_scraping_success(self, mock_get):
        """Test successful metadata extraction via web scraping."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <head>
            <meta itemprop="duration" content="PT3M34S">
        </head>
        <body>
            <script>
            var ytInitialData = {"title":"Test Video Title","ownerChannelName":"Test Channel"};
            </script>
        </body>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.extractor.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        expected = {
            'title': 'Test Video Title',
            'channel': 'Test Channel',
            'description': '',
            'published_at': '',
            'thumbnail_url': 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
            'video_id': 'dQw4w9WgXcQ',
            'duration': 214
        }
        
        assert result == expected
        mock_get.assert_called_once_with(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
            timeout=10
        )

    @patch('requests.get')
    def test_extract_metadata_via_scraping_no_duration(self, mock_get):
        """Test successful metadata extraction via web scraping when duration is missing."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <body>
            <script>
            var ytInitialData = {"title":"Test Video Title","ownerChannelName":"Test Channel"};
            </script>
        </body>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.extractor.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        expected = {
            'title': 'Test Video Title',
            'channel': 'Test Channel',
            'description': '',
            'published_at': '',
            'thumbnail_url': 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
            'video_id': 'dQw4w9WgXcQ',
            'duration': 0
        }

        assert result == expected
        mock_get.assert_called_once_with(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'},
            timeout=10
        )
    
    @patch('requests.get')
    def test_extract_metadata_via_scraping_video_unavailable(self, mock_get):
        """Test scraping when video is unavailable."""
        mock_response = Mock()
        mock_response.text = '<html>Video unavailable</html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with pytest.raises(VideoUnavailableError) as exc_info:
            self.extractor.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        assert "Video is not available" in str(exc_info.value)
        assert exc_info.value.video_id == "dQw4w9WgXcQ"
    
    @patch('requests.get')
    def test_extract_metadata_via_scraping_timeout(self, mock_get):
        """Test scraping with timeout error."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timed out")
        
        with pytest.raises(APIError) as exc_info:
            self.extractor.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        assert "Request timed out while scraping YouTube page" in str(exc_info.value)
        assert exc_info.value.api_name == "Web Scraping"
    
    @patch('requests.get')
    def test_extract_metadata_via_scraping_connection_error(self, mock_get):
        """Test scraping with connection error."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(APIError) as exc_info:
            self.extractor.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        assert "Connection error while scraping YouTube page" in str(exc_info.value)
        assert exc_info.value.api_name == "Web Scraping"
    
    @patch('requests.get')
    def test_extract_metadata_via_scraping_http_error(self, mock_get):
        """Test scraping with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        http_error = requests.exceptions.HTTPError("404 Not Found")
        http_error.response = mock_response
        mock_get.side_effect = http_error
        
        with pytest.raises(APIError) as exc_info:
            self.extractor.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        
        assert "HTTP error 404 while scraping YouTube page" in str(exc_info.value)
        assert exc_info.value.api_name == "Web Scraping"
    
    def test_extract_metadata_invalid_url(self):
        """Test metadata extraction with invalid URL."""
        with pytest.raises(InvalidURLError):
            self.extractor.extract_metadata("invalid_url")
    
    def test_extract_metadata_unexpected_error(self):
        """Test metadata extraction with unexpected error."""
        with patch.object(self.extractor, 'extract_video_id', side_effect=RuntimeError("Unexpected error")):
            with pytest.raises(MetadataExtractionError) as exc_info:
                self.extractor.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            
            assert "Unexpected error during metadata extraction" in str(exc_info.value)
    
    # Thumbnail URL Tests
    
    def test_construct_thumbnail_url(self):
        """Test thumbnail URL construction."""
        video_id = "dQw4w9WgXcQ"
        expected_url = "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg"
        
        result = self.extractor._construct_thumbnail_url(video_id)
        assert result == expected_url
    
    # Integration Tests
    
    def test_extract_metadata_chooses_api_when_available(self):
        """Test that API is used when available."""
        with patch.object(self.extractor_with_api, '_get_metadata_via_api') as mock_api, \
             patch.object(self.extractor_with_api, '_get_metadata_via_scraping') as mock_scraping:
            
            mock_api.return_value = {
                'title': 'Test Title',
                'channel': 'Test Channel',
                'description': '',
                'published_at': '',
                'thumbnail_url': 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg'
            }
            
            self.extractor_with_api.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            
            mock_api.assert_called_once_with("dQw4w9WgXcQ")
            mock_scraping.assert_not_called()
    
    def test_extract_metadata_falls_back_to_scraping(self):
        """Test that scraping is used when API key is not available."""
        with patch.object(self.extractor, '_get_metadata_via_api') as mock_api, \
             patch.object(self.extractor, '_get_metadata_via_scraping') as mock_scraping:
            
            mock_scraping.return_value = {
                'title': 'Test Title',
                'channel': 'Test Channel',
                'description': '',
                'published_at': '',
                'thumbnail_url': 'https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg'
            }
            
            self.extractor.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            
            mock_api.assert_not_called()
            mock_scraping.assert_called_once_with("dQw4w9WgXcQ")


    @patch('src.youtube_notion.extractors.video_metadata_extractor.build')
    def test_missing_metadata_fields_in_api_response(self, mock_build):
        """Test handling of missing fields in API response."""
        mock_youtube = Mock()
        mock_build.return_value = mock_youtube

        mock_request = Mock()
        mock_youtube.videos.return_value.list.return_value = mock_request

        # Response with missing fields
        mock_response = {
            'items': [{
                'snippet': {
                    # Missing title, channelTitle, etc.
                }
            }]
        }
        mock_request.execute.return_value = mock_response

        extractor = VideoMetadataExtractor(youtube_api_key="test_key")
        result = extractor.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # Should use default values for missing fields
        assert result['title'] == 'Unknown Title'
        assert result['channel'] == 'Unknown Channel'
        assert result['description'] == ''
        assert result['published_at'] == ''
        assert result['duration'] == 0

class TestVideoMetadataExtractorEdgeCases:
    """Test edge cases and error scenarios."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = VideoMetadataExtractor()
    
    @patch('requests.get')
    def test_unicode_handling_in_scraping(self, mock_get):
        """Test proper handling of unicode characters in scraped content."""
        mock_response = Mock()
        # Test with JSON-escaped unicode
        mock_response.text = '''
        <script>
        var data = {"title":"Test \\u2013 Video","ownerChannelName":"Test \\u00a9 Channel"};
        </script>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.extractor.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # The JSON decoder should properly handle unicode escapes
        assert 'Test' in result['title']
        assert 'Channel' in result['channel']
    
    @patch('requests.get')
    def test_malformed_json_in_scraping(self, mock_get):
        """Test handling of malformed JSON during scraping."""
        mock_response = Mock()
        # Malformed JSON that can't be decoded
        mock_response.text = '''
        <script>
        var data = {"title":"Test \\uXXXX Video","ownerChannelName":"Test Channel"};
        </script>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.extractor.extract_metadata("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

        # Should fall back to raw strings when JSON decoding fails
        assert 'title' in result
        assert 'channel' in result