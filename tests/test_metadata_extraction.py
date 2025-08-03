"""
Unit tests for YouTube metadata extraction functionality.

This module tests the video metadata extraction methods of the YouTubeProcessor,
including both YouTube Data API and web scraping approaches, as well as
thumbnail URL construction.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
from googleapiclient.errors import HttpError

from youtube_notion.processors.youtube_processor import YouTubeProcessor
from youtube_notion.processors.exceptions import (
    APIError,
    VideoUnavailableError,
    QuotaExceededError
)


class TestMetadataExtraction:
    """Test cases for video metadata extraction functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor_with_api = YouTubeProcessor.from_api_keys(gemini_api_key="test_gemini_key", youtube_api_key="test_youtube_key")
        self.processor_without_api = YouTubeProcessor.from_api_keys(
            gemini_api_key="test_gemini_key"
        )
        self.test_video_id = "dQw4w9WgXcQ"
        self.expected_metadata = {
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
        self.processor = YouTubeProcessor.from_api_keys(gemini_api_key="test_gemini_key", youtube_api_key="test_youtube_key")
        self.test_video_id = "dQw4w9WgXcQ"
    
    @patch('youtube_notion.processors.youtube_processor.build')
    def test_get_metadata_via_api_success(self, mock_build):
        """Test successful metadata extraction via YouTube Data API."""
        # Mock YouTube API response
        mock_youtube = Mock()
        mock_videos = Mock()
        mock_list = Mock()
        mock_request = Mock()
        
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
                }
            }]
        }
        
        # Execute method
        result = self.processor._get_metadata_via_api(self.test_video_id)
        
        # Verify API was called correctly
        mock_build.assert_called_once_with('youtube', 'v3', developerKey='test_youtube_key')
        mock_videos.list.assert_called_once_with(
            part='snippet',
            id=self.test_video_id
        )
        
        # Verify result
        expected = {
            'title': 'Rick Astley - Never Gonna Give You Up (Official Video)',
            'channel': 'RickAstleyVEVO',
            'description': 'The official video for "Never Gonna Give You Up"',
            'published_at': '2009-10-25T06:57:33Z',
            'thumbnail_url': f'https://img.youtube.com/vi/{self.test_video_id}/maxresdefault.jpg'
        }
        assert result == expected
    
    @patch('youtube_notion.processors.youtube_processor.build')
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
            self.processor._get_metadata_via_api(self.test_video_id)
        
        assert "Video not found or is not accessible" in str(exc_info.value)
        assert exc_info.value.video_id == self.test_video_id
    
    @patch('youtube_notion.processors.youtube_processor.build')
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
        mock_response = Mock()
        mock_response.status = 403
        error_details = [{'reason': 'quotaExceeded', 'message': 'Quota exceeded'}]
        http_error = HttpError(mock_response, b'Quota exceeded')
        http_error.error_details = error_details
        
        mock_list.execute.side_effect = http_error
        
        # Execute and verify exception
        with pytest.raises(QuotaExceededError) as exc_info:
            self.processor._get_metadata_via_api(self.test_video_id)
        
        assert "YouTube API quota exceeded" in str(exc_info.value)
        assert exc_info.value.api_name == "YouTube Data API"
        assert exc_info.value.quota_type == "per_minute"
    
    @patch('youtube_notion.processors.youtube_processor.build')
    def test_get_metadata_via_api_http_error(self, mock_build):
        """Test handling of general HTTP errors."""
        # Mock YouTube API HTTP error
        mock_youtube = Mock()
        mock_videos = Mock()
        mock_list = Mock()
        
        mock_build.return_value = mock_youtube
        mock_youtube.videos.return_value = mock_videos
        mock_videos.list.return_value = mock_list
        
        # Create HttpError for general API error
        mock_response = Mock()
        mock_response.status = 400
        error_details = [{'message': 'Bad Request'}]
        http_error = HttpError(mock_response, b'Bad Request')
        http_error.error_details = error_details
        
        mock_list.execute.side_effect = http_error
        
        # Execute and verify exception
        with pytest.raises(APIError) as exc_info:
            self.processor._get_metadata_via_api(self.test_video_id)
        
        assert "YouTube API request failed" in str(exc_info.value)
        assert exc_info.value.api_name == "YouTube Data API"
        assert exc_info.value.status_code == 400
    
    @patch('youtube_notion.processors.youtube_processor.build')
    def test_get_metadata_via_api_unexpected_error(self, mock_build):
        """Test handling of unexpected errors during API call."""
        # Mock unexpected exception
        mock_build.side_effect = Exception("Unexpected error")
        
        # Execute and verify exception
        with pytest.raises(APIError) as exc_info:
            self.processor._get_metadata_via_api(self.test_video_id)
        
        assert "Unexpected error during YouTube API call" in str(exc_info.value)
        assert exc_info.value.api_name == "YouTube Data API"


class TestWebScraping:
    """Test cases for web scraping metadata extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = YouTubeProcessor.from_api_keys(gemini_api_key="test_gemini_key")
        self.test_video_id = "dQw4w9WgXcQ"
    
    @patch('youtube_notion.processors.youtube_processor.requests.get')
    def test_get_metadata_via_scraping_success(self, mock_get):
        """Test successful metadata extraction via web scraping."""
        # Mock HTML response with video data
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <script>
        var ytInitialData = {
            "title": "Rick Astley - Never Gonna Give You Up (Official Video)",
            "ownerChannelName": "RickAstleyVEVO"
        };
        </script>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Execute method
        result = self.processor._get_metadata_via_scraping(self.test_video_id)
        
        # Verify request was made correctly
        expected_url = f"https://www.youtube.com/watch?v={self.test_video_id}"
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[0][0] == expected_url
        assert 'User-Agent' in call_args[1]['headers']
        assert call_args[1]['timeout'] == 10
        
        # Verify result structure
        assert 'title' in result
        assert 'channel' in result
        assert 'thumbnail_url' in result
        assert result['thumbnail_url'] == f'https://img.youtube.com/vi/{self.test_video_id}/maxresdefault.jpg'
    
    @patch('youtube_notion.processors.youtube_processor.requests.get')
    def test_get_metadata_via_scraping_video_unavailable(self, mock_get):
        """Test handling of unavailable video via web scraping."""
        # Mock HTML response indicating video is unavailable
        mock_response = Mock()
        mock_response.text = '<html><body>Video unavailable</body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Execute and verify exception
        with pytest.raises(VideoUnavailableError) as exc_info:
            self.processor._get_metadata_via_scraping(self.test_video_id)
        
        assert "Video is not available" in str(exc_info.value)
        assert exc_info.value.video_id == self.test_video_id
    
    @patch('youtube_notion.processors.youtube_processor.requests.get')
    def test_get_metadata_via_scraping_request_error(self, mock_get):
        """Test handling of request errors during web scraping."""
        # Mock request exception
        mock_get.side_effect = requests.RequestException("Connection failed")
        
        # Execute and verify exception
        with pytest.raises(APIError) as exc_info:
            self.processor._get_metadata_via_scraping(self.test_video_id)
        
        assert "Failed to scrape YouTube page" in str(exc_info.value)
        assert exc_info.value.api_name == "Web Scraping"
    
    @patch('youtube_notion.processors.youtube_processor.requests.get')
    def test_get_metadata_via_scraping_unexpected_error(self, mock_get):
        """Test handling of unexpected errors during web scraping."""
        # Mock unexpected exception
        mock_get.side_effect = Exception("Unexpected error")
        
        # Execute and verify exception
        with pytest.raises(APIError) as exc_info:
            self.processor._get_metadata_via_scraping(self.test_video_id)
        
        assert "Unexpected error during web scraping" in str(exc_info.value)
        assert exc_info.value.api_name == "Web Scraping"


class TestThumbnailConstruction:
    """Test cases for thumbnail URL construction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = YouTubeProcessor.from_api_keys(gemini_api_key="test_gemini_key")
    
    def test_construct_thumbnail_url(self):
        """Test thumbnail URL construction."""
        video_id = "dQw4w9WgXcQ"
        expected_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        
        result = self.processor._construct_thumbnail_url(video_id)
        
        assert result == expected_url
    
    def test_construct_thumbnail_url_different_video_ids(self):
        """Test thumbnail URL construction with different video IDs."""
        test_cases = [
            "dQw4w9WgXcQ",
            "jNQXAC9IVRw",
            "9bZkp7q19f0",
            "oHg5SJYRHA0"
        ]
        
        for video_id in test_cases:
            expected_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            result = self.processor._construct_thumbnail_url(video_id)
            assert result == expected_url


class TestUnicodeEncoding:
    """Test cases for unicode character encoding in metadata extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = YouTubeProcessor.from_api_keys(gemini_api_key="test_gemini_key")
        self.test_video_id = "test123"
    
    @patch('youtube_notion.processors.youtube_processor.requests.get')
    def test_web_scraping_em_dash_encoding(self, mock_get):
        """Test that em dash characters are correctly decoded in web scraping."""
        # Mock HTML with em dash as unicode escape sequence
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <script>
        "title":"Agents vs Workflows: Why Not Both? \\u2014 Sam Bhagwat, Mastra.ai","ownerChannelName":"Test Channel"
        </script>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.processor._get_metadata_via_scraping(self.test_video_id)
        
        # Verify em dash is correctly decoded
        expected_title = "Agents vs Workflows: Why Not Both? — Sam Bhagwat, Mastra.ai"
        assert result['title'] == expected_title
        assert result['channel'] == "Test Channel"
    
    @patch('youtube_notion.processors.youtube_processor.requests.get')
    def test_web_scraping_smart_quotes_encoding(self, mock_get):
        """Test that smart quotes are correctly decoded in web scraping."""
        # Mock HTML with smart quotes as unicode escape sequences
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <script>
        "title":"Testing \\u201cSmart Quotes\\u201d in Title","ownerChannelName":"Test Channel"
        </script>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.processor._get_metadata_via_scraping(self.test_video_id)
        
        # Verify smart quotes are correctly decoded (allow for different quote styles)
        assert "Smart Quotes" in result['title']
        assert len(result['title']) > len("Testing Smart Quotes in Title")  # Should have quote characters
        assert result['channel'] == "Test Channel"
    
    @patch('youtube_notion.processors.youtube_processor.requests.get')
    def test_web_scraping_accented_characters_encoding(self, mock_get):
        """Test that accented characters are correctly decoded in web scraping."""
        # Mock HTML with accented characters as unicode escape sequences
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <script>
        "title":"French Caf\\u00e9 and R\\u00e9sum\\u00e9","ownerChannelName":"Test Channel"
        </script>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.processor._get_metadata_via_scraping(self.test_video_id)
        
        # Verify accented characters are correctly decoded
        expected_title = "French Café and Résumé"
        assert result['title'] == expected_title
        assert result['channel'] == "Test Channel"
    
    @patch('youtube_notion.processors.youtube_processor.requests.get')
    def test_web_scraping_mathematical_symbols_encoding(self, mock_get):
        """Test that mathematical symbols are correctly decoded in web scraping."""
        # Mock HTML with mathematical symbols as unicode escape sequences
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <script>
        "title":"Math: \\u03b1 + \\u03b2 = \\u03b3","ownerChannelName":"Test Channel"
        </script>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.processor._get_metadata_via_scraping(self.test_video_id)
        
        # Verify mathematical symbols are correctly decoded
        expected_title = "Math: α + β = γ"
        assert result['title'] == expected_title
        assert result['channel'] == "Test Channel"
    
    @patch('youtube_notion.processors.youtube_processor.requests.get')
    def test_web_scraping_mixed_unicode_characters(self, mock_get):
        """Test that mixed unicode characters are correctly decoded in web scraping."""
        # Mock HTML with various unicode characters
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <script>
        "title":"Mixed: \\u2014 \\u201cQuotes\\u201d \\u00e9 \\u03b1","ownerChannelName":"Caf\\u00e9 Channel"
        </script>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.processor._get_metadata_via_scraping(self.test_video_id)
        
        # Verify all unicode characters are correctly decoded
        assert "—" in result['title']  # em dash
        assert "é" in result['title']  # accented e
        assert "α" in result['title']  # alpha
        assert "Café" in result['channel']  # accented e in channel
    
    @patch('youtube_notion.processors.youtube_processor.requests.get')
    def test_web_scraping_regular_ascii_unchanged(self, mock_get):
        """Test that regular ASCII characters remain unchanged."""
        # Mock HTML with regular ASCII characters
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <script>
        "title":"Regular ASCII Title with - dash","ownerChannelName":"Regular Channel"
        </script>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.processor._get_metadata_via_scraping(self.test_video_id)
        
        # Verify ASCII characters remain unchanged
        expected_title = "Regular ASCII Title with - dash"
        assert result['title'] == expected_title
        assert result['channel'] == "Regular Channel"
    
    @patch('youtube_notion.processors.youtube_processor.requests.get')
    def test_web_scraping_malformed_unicode_fallback(self, mock_get):
        """Test that malformed unicode sequences fall back gracefully."""
        # Mock HTML with malformed unicode escape sequences
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <script>
        "title":"Malformed \\u201 incomplete","ownerChannelName":"Test Channel"
        </script>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.processor._get_metadata_via_scraping(self.test_video_id)
        
        # Verify that malformed sequences fall back to raw strings
        assert "Malformed" in result['title']
        assert result['channel'] == "Test Channel"
    
    @patch('youtube_notion.processors.youtube_processor.build')
    def test_api_unicode_preservation(self, mock_build):
        """Test that YouTube API correctly preserves unicode characters."""
        # Mock YouTube API response with unicode characters
        mock_youtube = Mock()
        mock_videos = Mock()
        mock_list = Mock()
        mock_request = Mock()
        
        mock_build.return_value = mock_youtube
        mock_youtube.videos.return_value = mock_videos
        mock_videos.list.return_value = mock_list
        mock_list.execute.return_value = {
            'items': [{
                'snippet': {
                    'title': 'Agents vs Workflows: Why Not Both? — Sam Bhagwat, Mastra.ai',
                    'channelTitle': 'Café Channel',
                    'description': 'Test description with α symbols',
                    'publishedAt': '2023-01-01T00:00:00Z'
                }
            }]
        }
        
        # Create processor with API key
        processor_with_api = YouTubeProcessor.from_api_keys(
            gemini_api_key="test_gemini_key", 
            youtube_api_key="test_youtube_key"
        )
        
        result = processor_with_api._get_metadata_via_api(self.test_video_id)
        
        # Verify unicode characters are preserved from API
        expected_title = "Agents vs Workflows: Why Not Both? — Sam Bhagwat, Mastra.ai"
        assert result['title'] == expected_title
        assert result['channel'] == "Café Channel"
        assert result['description'] == "Test description with α symbols"
    
    @patch('youtube_notion.processors.youtube_processor.requests.get')
    def test_web_scraping_channel_name_encoding(self, mock_get):
        """Test that channel names with unicode characters are correctly decoded."""
        # Mock HTML with unicode characters in channel name
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <script>
        "title":"Regular Title","ownerChannelName":"Caf\\u00e9 \\u2014 Channel"
        </script>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = self.processor._get_metadata_via_scraping(self.test_video_id)
        
        # Verify channel name unicode characters are correctly decoded
        expected_channel = "Café — Channel"
        assert result['title'] == "Regular Title"
        assert result['channel'] == expected_channel


class TestMetadataExtractionIntegration:
    """Integration tests for metadata extraction methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor_with_api = YouTubeProcessor.from_api_keys(gemini_api_key="test_gemini_key", youtube_api_key="test_youtube_key")
        self.processor_without_api = YouTubeProcessor.from_api_keys(
            gemini_api_key="test_gemini_key"
        )
        self.test_video_id = "dQw4w9WgXcQ"
    
    @patch('youtube_notion.processors.youtube_processor.YouTubeProcessor._get_metadata_via_api')
    def test_get_video_metadata_with_api_key(self, mock_api_method):
        """Test that _get_video_metadata uses API when key is available."""
        mock_api_method.return_value = {'title': 'Test Video', 'channel': 'Test Channel'}
        
        result = self.processor_with_api._get_video_metadata(self.test_video_id)
        
        mock_api_method.assert_called_once_with(self.test_video_id)
        assert result == {'title': 'Test Video', 'channel': 'Test Channel'}
    
    @patch('youtube_notion.processors.youtube_processor.YouTubeProcessor._get_metadata_via_scraping')
    def test_get_video_metadata_without_api_key(self, mock_scraping_method):
        """Test that _get_video_metadata uses scraping when no API key."""
        mock_scraping_method.return_value = {'title': 'Test Video', 'channel': 'Test Channel'}
        
        result = self.processor_without_api._get_video_metadata(self.test_video_id)
        
        mock_scraping_method.assert_called_once_with(self.test_video_id)
        assert result == {'title': 'Test Video', 'channel': 'Test Channel'}