"""
Unit tests for YouTube metadata extraction functionality.

This module tests the video metadata extraction methods of the VideoMetadataExtractor,
including both YouTube Data API and web scraping approaches, as well as
thumbnail URL construction.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from googleapiclient.errors import HttpError

from src.youtube_notion.extractors.video_metadata_extractor import VideoMetadataExtractor
from src.youtube_notion.utils.exceptions import (
    APIError,
    VideoUnavailableError,
    QuotaExceededError,
    InvalidURLError
)


class TestMetadataExtraction:
    """Test cases for video metadata extraction functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor_with_api = VideoMetadataExtractor(youtube_api_key="test_youtube_key")
        self.extractor_without_api = VideoMetadataExtractor(youtube_api_key=None)
        self.test_video_id = "dQw4w9WgXcQ"
        self.expected_metadata = {
            'video_id': 'dQw4w9WgXcQ',
            'title': 'Rick Astley - Never Gonna Give You Up (Official Video)',
            'channel': 'RickAstleyVEVO',
            'description': 'The official video for "Never Gonna Give You Up"',
            'published_at': '2009-10-25T06:57:33Z',
            'thumbnail_url': f'https://img.youtube.com/vi/{self.test_video_id}/maxresdefault.jpg'
        }


class TestYouTubeDataAPI:
    """Test cases for YouTube Data API metadata extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = VideoMetadataExtractor(youtube_api_key="test_youtube_key")
        self.test_video_id = "dQw4w9WgXcQ"
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.build')
    def test_get_metadata_via_api_success(self, mock_build):
        """Test successful metadata extraction via YouTube Data API."""
        # Mock YouTube API response
        mock_youtube = Mock()
        mock_videos = Mock()
        mock_list = Mock()
        
        mock_build.return_value = mock_youtube
        mock_youtube.videos.return_value = mock_videos
        mock_videos.list.return_value = mock_list
        mock_list.execute.return_value = {
            'items': [{
                'snippet': {
                    'title': 'Rick Astley - Never Gonna Give You Up (Official Video)',
                    'channelTitle': 'RickAstleyVEVO',
                    'description': 'The official video for "Never Gonna Give You Up"',
                    'publishedAt': '2009-10-25T06:57:33Z'
                },
                'contentDetails': {
                    'duration': 'PT3M32S'
                }
            }]
        }
        
        # Execute method
        result = self.extractor._get_metadata_via_api(self.test_video_id)
        
        # Verify API was called correctly
        mock_build.assert_called_once_with('youtube', 'v3', developerKey='test_youtube_key')
        mock_videos.list.assert_called_once_with(
            part='snippet,contentDetails',
            id=self.test_video_id
        )
        
        # Verify result
        expected = {
            'title': 'Rick Astley - Never Gonna Give You Up (Official Video)',
            'channel': 'RickAstleyVEVO',
            'description': 'The official video for "Never Gonna Give You Up"',
            'published_at': '2009-10-25T06:57:33Z',
            'thumbnail_url': f'https://img.youtube.com/vi/{self.test_video_id}/maxresdefault.jpg',
            'duration': 212
        }
        assert result == expected
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.build')
    def test_get_metadata_via_api_video_not_found(self, mock_build):
        """Test handling of video not found via YouTube Data API."""
        # Mock YouTube API response with empty items
        mock_youtube = Mock()
        mock_videos = Mock()
        mock_list = Mock()
        
        mock_build.return_value = mock_youtube
        mock_youtube.videos.return_value = mock_videos
        mock_videos.list.return_value = mock_list
        mock_list.execute.return_value = {'items': []}
        
        # Execute and verify exception
        with pytest.raises(VideoUnavailableError) as exc_info:
            self.extractor._get_metadata_via_api(self.test_video_id)
        
        assert "Video not found or is not accessible" in str(exc_info.value)
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.build')
    def test_get_metadata_via_api_quota_exceeded(self, mock_build):
        """Test handling of quota exceeded error."""
        # Mock YouTube API quota exceeded error
        mock_youtube = Mock()
        mock_videos = Mock()
        mock_list = Mock()
        
        mock_build.return_value = mock_youtube
        mock_youtube.videos.return_value = mock_videos
        mock_videos.list.return_value = mock_list
        
        # Create HttpError for quota exceeded
        error_content = b'{"error": {"code": 403, "message": "quotaExceeded", "errors": [{"reason": "quotaExceeded"}]}}'
        http_error = HttpError(
            resp=Mock(status=403, reason='Forbidden'),
            content=error_content
        )
        mock_list.execute.side_effect = http_error
        
        # Execute and verify exception
        with pytest.raises(QuotaExceededError) as exc_info:
            self.extractor._get_metadata_via_api(self.test_video_id)
        
        assert "YouTube API quota exceeded" in str(exc_info.value)
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.build')
    def test_get_metadata_via_api_http_error(self, mock_build):
        """Test handling of general HTTP errors."""
        # Mock YouTube API HTTP error
        mock_youtube = Mock()
        mock_videos = Mock()
        mock_list = Mock()
        
        mock_build.return_value = mock_youtube
        mock_youtube.videos.return_value = mock_videos
        mock_videos.list.return_value = mock_list
        
        # Create HttpError for general error
        error_content = b'{"error": {"code": 400, "message": "badRequest", "errors": [{"reason": "badRequest"}]}}'
        http_error = HttpError(
            resp=Mock(status=400, reason='Bad Request'),
            content=error_content
        )
        mock_list.execute.side_effect = http_error
        
        # Execute and verify exception
        with pytest.raises(APIError) as exc_info:
            self.extractor._get_metadata_via_api(self.test_video_id)
        
        assert "YouTube API request failed" in str(exc_info.value)
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.build')
    def test_get_metadata_via_api_unexpected_error(self, mock_build):
        """Test handling of unexpected errors during API call."""
        # Mock unexpected exception
        mock_build.side_effect = Exception("Unexpected error")
        
        # Execute and verify exception
        with pytest.raises(APIError) as exc_info:
            self.extractor._get_metadata_via_api(self.test_video_id)
        
        assert "Unexpected error during YouTube API call" in str(exc_info.value)


class TestWebScraping:
    """Test cases for web scraping metadata extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = VideoMetadataExtractor(youtube_api_key=None)
        self.test_video_id = "dQw4w9WgXcQ"
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_get_metadata_via_scraping_success(self, mock_get):
        """Test successful metadata extraction via web scraping."""
        # Mock successful HTTP response with YouTube page content (JSON format)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
        {"title":"Rick Astley - Never Gonna Give You Up (Official Video)","ownerChannelName":"RickAstleyVEVO"}
        '''
        mock_get.return_value = mock_response
        
        # Execute method
        result = self.extractor._get_metadata_via_scraping(self.test_video_id)
        
        # Verify HTTP request was made with correct parameters
        expected_url = f"https://www.youtube.com/watch?v={self.test_video_id}"
        expected_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        mock_get.assert_called_once_with(expected_url, headers=expected_headers, timeout=10)
        
        # Verify result structure
        assert isinstance(result, dict)
        assert 'title' in result
        assert 'channel' in result
        assert 'description' in result
        assert 'published_at' in result
        assert 'thumbnail_url' in result
        
        # Verify extracted content
        assert result['title'] == "Rick Astley - Never Gonna Give You Up (Official Video)"
        assert result['channel'] == "RickAstleyVEVO"
        
        # Verify thumbnail URL is constructed correctly
        expected_thumbnail = f'https://img.youtube.com/vi/{self.test_video_id}/maxresdefault.jpg'
        assert result['thumbnail_url'] == expected_thumbnail
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_get_metadata_via_scraping_video_unavailable(self, mock_get):
        """Test handling of unavailable video during web scraping."""
        # Mock HTTP response for unavailable video
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'Video unavailable - This video is not available'
        mock_get.return_value = mock_response
        
        # Execute and verify exception
        with pytest.raises(VideoUnavailableError) as exc_info:
            self.extractor._get_metadata_via_scraping(self.test_video_id)
        
        assert "Video is not available" in str(exc_info.value)
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_get_metadata_via_scraping_request_error(self, mock_get):
        """Test handling of request errors during web scraping."""
        # Mock request exception
        mock_get.side_effect = requests.RequestException("Network error")
        
        # Execute and verify exception
        with pytest.raises(APIError) as exc_info:
            self.extractor._get_metadata_via_scraping(self.test_video_id)
        
        assert "Failed to scrape YouTube page" in str(exc_info.value)
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_get_metadata_via_scraping_unexpected_error(self, mock_get):
        """Test handling of unexpected errors during web scraping."""
        # Mock unexpected exception
        mock_get.side_effect = Exception("Unexpected error")
        
        # Execute and verify exception
        with pytest.raises(APIError) as exc_info:
            self.extractor._get_metadata_via_scraping(self.test_video_id)
        
        assert "Unexpected error during web scraping" in str(exc_info.value)


class TestUnicodeEncoding:
    """Test cases for Unicode character handling in metadata extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor_with_api = VideoMetadataExtractor(youtube_api_key="test_youtube_key")
        self.extractor_without_api = VideoMetadataExtractor(youtube_api_key=None)
        self.test_video_id = "dQw4w9WgXcQ"
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_web_scraping_em_dash_encoding(self, mock_get):
        """Test that em dashes are properly handled in web scraping."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"title":"Test Video — Special Characters","ownerChannelName":"Test Channel"}'
        mock_get.return_value = mock_response
        
        result = self.extractor_without_api._get_metadata_via_scraping(self.test_video_id)
        
        # Verify em dash is preserved
        assert "—" in result['title']
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_web_scraping_smart_quotes_encoding(self, mock_get):
        """Test that smart quotes are properly handled in web scraping."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Use escaped quotes in JSON to make it valid
        mock_response.text = '{"title":"Test Video \u201cSmart Quotes\u201d","ownerChannelName":"Test Channel"}'
        mock_get.return_value = mock_response
        
        result = self.extractor_without_api._get_metadata_via_scraping(self.test_video_id)
        
        # Verify smart quotes are preserved (JSON decoder converts Unicode escapes)
        assert "Smart Quotes" in result['title']
        # The actual characters should be present after JSON decoding
        # \u201c is left double quotation mark, \u201d is right double quotation mark
        assert "\u201c" in result['title'] and "\u201d" in result['title']
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_web_scraping_accented_characters_encoding(self, mock_get):
        """Test that accented characters are properly handled in web scraping."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"title":"Café Français","ownerChannelName":"Chaîne Française"}'
        mock_get.return_value = mock_response
        
        result = self.extractor_without_api._get_metadata_via_scraping(self.test_video_id)
        
        # Verify accented characters are preserved
        assert "Café" in result['title']
        assert "Français" in result['title']
        assert "Chaîne" in result['channel']
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_web_scraping_mathematical_symbols_encoding(self, mock_get):
        """Test that mathematical symbols are properly handled in web scraping."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"title":"Math: α + β = γ","ownerChannelName":"Math Channel"}'
        mock_get.return_value = mock_response
        
        result = self.extractor_without_api._get_metadata_via_scraping(self.test_video_id)
        
        # Verify mathematical symbols are preserved
        assert "α" in result['title']
        assert "β" in result['title']
        assert "γ" in result['title']
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_web_scraping_mixed_unicode_characters(self, mock_get):
        """Test handling of mixed Unicode characters in web scraping."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"title":"Test Video with Unicode: 你好世界 🎵","ownerChannelName":"Unicode Channel"}'
        mock_get.return_value = mock_response
        
        result = self.extractor_without_api._get_metadata_via_scraping(self.test_video_id)
        
        # Verify mixed Unicode characters are preserved
        assert "你好世界" in result['title']
        assert "🎵" in result['title']
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_web_scraping_regular_ascii_unchanged(self, mock_get):
        """Test that regular ASCII characters remain unchanged in web scraping."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"title":"Regular ASCII Title","ownerChannelName":"Regular Channel"}'
        mock_get.return_value = mock_response
        
        result = self.extractor_without_api._get_metadata_via_scraping(self.test_video_id)
        
        # Verify ASCII characters are unchanged
        assert result['title'] == "Regular ASCII Title"
        assert result['channel'] == "Regular Channel"
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_web_scraping_malformed_unicode_fallback(self, mock_get):
        """Test graceful handling of malformed Unicode in web scraping."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Simulate malformed Unicode by using bytes that don't decode properly
        mock_response.text = 'Test Title with \udcff invalid Unicode'
        mock_get.return_value = mock_response
        
        # Should not raise an exception, but handle gracefully
        result = self.extractor_without_api._get_metadata_via_scraping(self.test_video_id)
        
        # Verify result is still a valid dictionary
        assert isinstance(result, dict)
        assert 'title' in result
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.build')
    def test_api_unicode_preservation(self, mock_build):
        """Test that Unicode characters are preserved from API responses."""
        # Mock YouTube API response with Unicode characters
        mock_youtube = Mock()
        mock_videos = Mock()
        mock_list = Mock()
        
        mock_build.return_value = mock_youtube
        mock_youtube.videos.return_value = mock_videos
        mock_videos.list.return_value = mock_list
        mock_list.execute.return_value = {
            'items': [{
                'snippet': {
                    'title': 'Test Video with Unicode: 你好世界 🎵',
                    'channelTitle': 'Unicode Channel',
                    'description': 'Description with émojis and açcénts',
                    'publishedAt': '2023-01-01T00:00:00Z'
                }
            }]
        }
        
        result = self.extractor_with_api._get_metadata_via_api(self.test_video_id)
        
        # Verify unicode characters are preserved from API
        assert "你好世界" in result['title']
        assert "🎵" in result['title']
        assert "émojis" in result['description']
        assert "açcénts" in result['description']
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_web_scraping_channel_name_encoding(self, mock_get):
        """Test that channel names with special characters are handled correctly."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"title":"Test Video","ownerChannelName":"Chaîne Spécialisée™"}'
        mock_get.return_value = mock_response
        
        result = self.extractor_without_api._get_metadata_via_scraping(self.test_video_id)
        
        # Verify special characters in channel name are preserved
        assert "Chaîne" in result['channel']
        assert "Spécialisée" in result['channel']
        assert "™" in result['channel']


class TestMetadataExtractionIntegration:
    """Integration tests for metadata extraction workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_video_id = "dQw4w9WgXcQ"
    
    def test_get_video_metadata_with_api_key(self):
        """Test that _get_video_metadata uses API when key is available."""
        extractor = VideoMetadataExtractor(youtube_api_key="test_key")
        
        with patch.object(extractor, '_get_metadata_via_api') as mock_api, \
             patch.object(extractor, '_get_metadata_via_scraping') as mock_scraping:
            
            mock_api.return_value = {'title': 'Test', 'channel': 'Test Channel'}
            
            result = extractor._get_video_metadata(self.test_video_id)
            
            # Verify API method was called, not scraping
            mock_api.assert_called_once_with(self.test_video_id)
            mock_scraping.assert_not_called()
            
            assert result['title'] == 'Test'
    
    def test_get_video_metadata_without_api_key(self):
        """Test that _get_video_metadata uses scraping when no API key."""
        extractor = VideoMetadataExtractor(youtube_api_key=None)
        
        with patch.object(extractor, '_get_metadata_via_api') as mock_api, \
             patch.object(extractor, '_get_metadata_via_scraping') as mock_scraping:
            
            mock_scraping.return_value = {'title': 'Test', 'channel': 'Test Channel'}
            
            result = extractor._get_video_metadata(self.test_video_id)
            
            # Verify scraping method was called, not API
            mock_scraping.assert_called_once_with(self.test_video_id)
            mock_api.assert_not_called()
            
            assert result['title'] == 'Test'
    
    def test_thumbnail_url_construction(self):
        """Test thumbnail URL construction."""
        extractor = VideoMetadataExtractor(youtube_api_key=None)
        
        result = extractor._construct_thumbnail_url(self.test_video_id)
        
        expected = f'https://img.youtube.com/vi/{self.test_video_id}/maxresdefault.jpg'
        assert result == expected
    
    def test_video_id_validation_valid_ids(self):
        """Test video ID validation with valid IDs."""
        extractor = VideoMetadataExtractor(youtube_api_key=None)
        
        valid_ids = [
            "dQw4w9WgXcQ",  # 11 characters, alphanumeric (real YouTube ID)
            "abc123DEF45",  # 11 characters, mixed case
            "test-video_",  # 11 characters with hyphen and underscore
            "test_video1",  # 11 characters with underscore and number
        ]
        
        for video_id in valid_ids:
            assert extractor._is_valid_video_id(video_id) is True
    
    def test_video_id_validation_invalid_ids(self):
        """Test video ID validation with invalid IDs."""
        extractor = VideoMetadataExtractor(youtube_api_key=None)
        
        invalid_ids = [
            "short",        # Too short
            "toolongvideoid123",  # Too long
            "",             # Empty
            None,           # None
            "test video",   # Contains space
            "test@video",   # Contains invalid character
        ]
        
        for video_id in invalid_ids:
            assert extractor._is_valid_video_id(video_id) is False