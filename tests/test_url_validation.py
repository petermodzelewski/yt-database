"""
Unit tests for YouTube URL validation and video ID extraction.

This module tests the URL parsing functionality of the YouTubeProcessor,
including various YouTube URL formats, edge cases, and error scenarios.
"""

import pytest
from youtube_notion.processors.youtube_processor import YouTubeProcessor
from youtube_notion.processors.exceptions import InvalidURLError


class TestURLValidation:
    """Test cases for YouTube URL validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = YouTubeProcessor.from_api_keys(gemini_api_key="test_key")
    
    def test_validate_youtube_url_valid_urls(self):
        """Test validation of valid YouTube URLs."""
        valid_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "www.youtube.com/watch?v=dQw4w9WgXcQ",
            "youtube.com/watch?v=dQw4w9WgXcQ",
            "youtu.be/dQw4w9WgXcQ",
        ]
        
        for url in valid_urls:
            assert self.processor.validate_youtube_url(url), f"URL should be valid: {url}"
    
    def test_validate_youtube_url_invalid_urls(self):
        """Test validation of invalid URLs."""
        invalid_urls = [
            "https://vimeo.com/123456789",
            "https://www.dailymotion.com/video/x123456",
            "https://www.facebook.com/watch?v=123456789",
            "https://example.com/watch?v=dQw4w9WgXcQ",
            "not_a_url",
            "",
            None,
            123,
            "https://youtube.com/",
            "https://youtube.com/watch",
            "https://youtube.com/watch?v=",
            "https://youtube.com/watch?v=invalid_id",
        ]
        
        for url in invalid_urls:
            assert not self.processor.validate_youtube_url(url), f"URL should be invalid: {url}"


class TestVideoIDExtraction:
    """Test cases for video ID extraction from YouTube URLs."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = YouTubeProcessor.from_api_keys(gemini_api_key="test_key")
        self.test_video_id = "dQw4w9WgXcQ"
    
    def test_extract_video_id_standard_urls(self):
        """Test extraction from standard YouTube URLs."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://m.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("http://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            result = self.processor._extract_video_id(url)
            assert result == expected_id, f"Expected {expected_id}, got {result} for URL: {url}"
    
    def test_extract_video_id_short_urls(self):
        """Test extraction from youtu.be short URLs."""
        test_cases = [
            ("https://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("http://youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            result = self.processor._extract_video_id(url)
            assert result == expected_id, f"Expected {expected_id}, got {result} for URL: {url}"
    
    def test_extract_video_id_with_parameters(self):
        """Test extraction from URLs with additional parameters."""
        test_cases = [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=123s", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmRdnEQy6nuLMHjMZOz59Oq3KuQEl", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=youtu.be", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ?t=123", "dQw4w9WgXcQ"),
            ("https://youtu.be/dQw4w9WgXcQ?si=abc123", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            result = self.processor._extract_video_id(url)
            assert result == expected_id, f"Expected {expected_id}, got {result} for URL: {url}"
    
    def test_extract_video_id_embed_urls(self):
        """Test extraction from embed URLs."""
        test_cases = [
            ("https://www.youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/embed/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://www.youtube.com/embed/dQw4w9WgXcQ?start=123", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            result = self.processor._extract_video_id(url)
            assert result == expected_id, f"Expected {expected_id}, got {result} for URL: {url}"
    
    def test_extract_video_id_legacy_urls(self):
        """Test extraction from legacy /v/ URLs."""
        test_cases = [
            ("https://www.youtube.com/v/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("https://youtube.com/v/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            result = self.processor._extract_video_id(url)
            assert result == expected_id, f"Expected {expected_id}, got {result} for URL: {url}"
    
    def test_extract_video_id_no_protocol(self):
        """Test extraction from URLs without protocol."""
        test_cases = [
            ("www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            ("youtu.be/dQw4w9WgXcQ", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            result = self.processor._extract_video_id(url)
            assert result == expected_id, f"Expected {expected_id}, got {result} for URL: {url}"
    
    def test_extract_video_id_with_whitespace(self):
        """Test extraction from URLs with whitespace."""
        test_cases = [
            ("  https://www.youtube.com/watch?v=dQw4w9WgXcQ  ", "dQw4w9WgXcQ"),
            ("\thttps://youtu.be/dQw4w9WgXcQ\n", "dQw4w9WgXcQ"),
        ]
        
        for url, expected_id in test_cases:
            result = self.processor._extract_video_id(url)
            assert result == expected_id, f"Expected {expected_id}, got {result} for URL: {url}"


class TestVideoIDExtractionErrors:
    """Test cases for error scenarios in video ID extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = YouTubeProcessor.from_api_keys(gemini_api_key="test_key")
    
    def test_extract_video_id_invalid_input_types(self):
        """Test extraction with invalid input types."""
        invalid_inputs = [None, 123, [], {}, True]
        
        for invalid_input in invalid_inputs:
            with pytest.raises(InvalidURLError) as exc_info:
                self.processor._extract_video_id(invalid_input)
            assert "URL must be a non-empty string" in str(exc_info.value)
    
    def test_extract_video_id_empty_string(self):
        """Test extraction with empty string."""
        with pytest.raises(InvalidURLError) as exc_info:
            self.processor._extract_video_id("")
        assert "URL must be a non-empty string" in str(exc_info.value)
    
    def test_extract_video_id_invalid_domains(self):
        """Test extraction from non-YouTube domains."""
        invalid_domains = [
            "https://vimeo.com/123456789",
            "https://www.dailymotion.com/video/x123456",
            "https://example.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.evil.com/watch?v=dQw4w9WgXcQ",
        ]
        
        for url in invalid_domains:
            with pytest.raises(InvalidURLError) as exc_info:
                self.processor._extract_video_id(url)
            assert "not from a supported YouTube domain" in str(exc_info.value)
    
    def test_extract_video_id_malformed_urls(self):
        """Test extraction from malformed URLs."""
        malformed_urls = [
            "not_a_url",
            "https://",
            "://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch",
            "https://youtube.com/watch?v=",
            "https://youtu.be/",
        ]
        
        for url in malformed_urls:
            with pytest.raises(InvalidURLError):
                self.processor._extract_video_id(url)
    
    def test_extract_video_id_invalid_video_ids(self):
        """Test extraction with invalid video ID formats."""
        invalid_video_ids = [
            "https://youtube.com/watch?v=short",  # Too short
            "https://youtube.com/watch?v=toolongvideoid123",  # Too long
            "https://youtube.com/watch?v=invalid@id!",  # Invalid characters
            "https://youtu.be/123456789a",  # Too short (10 chars)
            "https://youtu.be/123456789abc",  # Too long (12 chars)
            "https://youtu.be/12345+67890",  # Invalid character (+)
        ]
        
        for url in invalid_video_ids:
            with pytest.raises(InvalidURLError) as exc_info:
                self.processor._extract_video_id(url)
            assert "invalid format" in str(exc_info.value)


class TestVideoIDValidation:
    """Test cases for video ID format validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = YouTubeProcessor.from_api_keys(gemini_api_key="test_key")
    
    def test_is_valid_video_id_valid_ids(self):
        """Test validation of valid video IDs."""
        valid_ids = [
            "dQw4w9WgXcQ",  # Standard video ID
            "jNQXAC9IVRw",  # Another real video ID
            "9bZkp7q19f0",  # Video ID with numbers
            "abc123DEF-_",  # All valid characters
            "___________",  # All underscores
            "-----------",  # All hyphens
            "12345678901",  # All numbers
            "ABCDEFGHIJK",  # All uppercase
            "abcdefghijk",  # All lowercase
        ]
        
        for video_id in valid_ids:
            assert self.processor._is_valid_video_id(video_id), f"Video ID should be valid: {video_id}"
    
    def test_is_valid_video_id_invalid_ids(self):
        """Test validation of invalid video IDs."""
        invalid_ids = [
            "",  # Empty string
            None,  # None
            123,  # Not a string
            "short",  # Too short
            "toolongvideoid123",  # Too long
            "invalid@id!",  # Invalid characters
            "dQw4w9WgXc ",  # Contains space
            "dQw4w9WgXc\n",  # Contains newline
            "dQw4w9WgXc+",  # Contains plus
            "dQw4w9WgXc=",  # Contains equals
            "dQw4w9WgXc/",  # Contains slash
        ]
        
        for video_id in invalid_ids:
            assert not self.processor._is_valid_video_id(video_id), f"Video ID should be invalid: {video_id}"
    
    def test_is_valid_video_id_edge_cases(self):
        """Test validation edge cases."""
        # Test exactly 11 characters with mixed valid characters
        edge_cases = [
            ("a1b2c3d4e5f", True),  # Mixed alphanumeric
            ("A1B2C3D4E5F", True),  # Mixed with uppercase
            ("a-b_c1d2e3f", True),  # With hyphens and underscores
            ("___---___--", True),  # Only special characters
            ("12345678901", True),  # Only numbers
            ("abcdefghijk", True),  # Only lowercase letters
            ("ABCDEFGHIJK", True),  # Only uppercase letters
        ]
        
        for video_id, expected in edge_cases:
            result = self.processor._is_valid_video_id(video_id)
            assert result == expected, f"Video ID {video_id} should be {expected}, got {result}"


class TestIntegrationScenarios:
    """Integration test scenarios combining URL validation and ID extraction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = YouTubeProcessor.from_api_keys(gemini_api_key="test_key")
    
    def test_real_youtube_urls(self):
        """Test with real YouTube URLs and their expected video IDs."""
        real_urls = [
            # Rick Astley - Never Gonna Give You Up
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ"),
            # Gangnam Style
            ("https://www.youtube.com/watch?v=9bZkp7q19f0", "9bZkp7q19f0"),
            # Despacito
            ("https://www.youtube.com/watch?v=kJQP7kiw5Fk", "kJQP7kiw5Fk"),
        ]
        
        for url, expected_id in real_urls:
            # Test validation
            assert self.processor.validate_youtube_url(url), f"URL should be valid: {url}"
            
            # Test extraction
            extracted_id = self.processor._extract_video_id(url)
            assert extracted_id == expected_id, f"Expected {expected_id}, got {extracted_id}"
    
    def test_url_variations_same_video(self):
        """Test that different URL formats for the same video return the same ID."""
        video_id = "dQw4w9WgXcQ"
        url_variations = [
            f"https://www.youtube.com/watch?v={video_id}",
            f"https://youtube.com/watch?v={video_id}",
            f"https://m.youtube.com/watch?v={video_id}",
            f"https://youtu.be/{video_id}",
            f"https://www.youtube.com/embed/{video_id}",
            f"https://www.youtube.com/v/{video_id}",
            f"www.youtube.com/watch?v={video_id}",
            f"youtu.be/{video_id}",
            f"https://www.youtube.com/watch?v={video_id}&t=123s",
            f"https://youtu.be/{video_id}?t=123",
        ]
        
        for url in url_variations:
            extracted_id = self.processor._extract_video_id(url)
            assert extracted_id == video_id, f"URL {url} should extract to {video_id}, got {extracted_id}"
    
    def test_error_consistency(self):
        """Test that validation and extraction errors are consistent."""
        invalid_urls = [
            "https://vimeo.com/123456789",
            "not_a_url",
            "",
            "https://youtube.com/watch?v=invalid",
        ]
        
        for url in invalid_urls:
            # Validation should return False
            assert not self.processor.validate_youtube_url(url), f"URL should be invalid: {url}"
            
            # Extraction should raise InvalidURLError
            with pytest.raises(InvalidURLError):
                self.processor._extract_video_id(url)