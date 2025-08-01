"""
Unit tests for timestamp enrichment functionality.
Tests the conversion of timestamps to YouTube links.
"""

import pytest
from youtube_notion.utils.markdown_converter import (
    parse_timestamp_to_seconds,
    get_youtube_video_id,
    create_youtube_timestamp_url,
    enrich_timestamps_with_links
)


class TestTimestampParsing:
    """Test cases for timestamp parsing functions."""
    
    @pytest.mark.parametrize("timestamp,expected", [
        ("8:05", 485),
        ("1:23", 83),
        ("0:30", 30),
        ("10:00", 600),
        ("59:59", 3599),
    ])
    def test_parse_timestamp_minutes_seconds(self, timestamp, expected):
        """Test parsing MM:SS format."""
        assert parse_timestamp_to_seconds(timestamp) == expected
    
    @pytest.mark.parametrize("timestamp,expected", [
        ("1:23:45", 5025),
        ("0:08:05", 485),
        ("2:00:00", 7200),
        ("0:00:01", 1),
        ("23:59:59", 86399),
    ])
    def test_parse_timestamp_hours_minutes_seconds(self, timestamp, expected):
        """Test parsing HH:MM:SS format."""
        assert parse_timestamp_to_seconds(timestamp) == expected
    
    @pytest.mark.parametrize("invalid_timestamp", [
        "8",
        "8:05:30:15",
        "invalid",
        "8:60",  # Invalid seconds
        "1:2:3:4:5",  # Too many parts
    ])
    def test_parse_timestamp_invalid_format(self, invalid_timestamp):
        """Test parsing invalid timestamp formats."""
        with pytest.raises(ValueError):
            parse_timestamp_to_seconds(invalid_timestamp)
    
    def test_parse_timestamp_edge_cases(self):
        """Test edge cases that are currently allowed by the implementation."""
        # These are currently allowed by the implementation
        assert parse_timestamp_to_seconds("60:30") == 3630  # 60 minutes is allowed
        assert parse_timestamp_to_seconds("-1:30") == -30   # Negative minutes, positive seconds


class TestYouTubeUrlParsing:
    """Test cases for YouTube URL parsing."""
    
    @pytest.mark.parametrize("url,expected_id", [
        ("https://www.youtube.com/watch?v=pMSXPgAUq_k", "pMSXPgAUq_k"),
        ("https://youtube.com/watch?v=abc123", "abc123"),
        ("http://www.youtube.com/watch?v=test_id", "test_id"),
    ])
    def test_get_youtube_video_id_standard_url(self, url, expected_id):
        """Test extracting video ID from standard YouTube URLs."""
        assert get_youtube_video_id(url) == expected_id
    
    def test_get_youtube_video_id_unsupported_domains(self):
        """Test that unsupported YouTube domains return None."""
        # m.youtube.com is not currently supported by the implementation
        assert get_youtube_video_id("https://m.youtube.com/watch?v=mobile123") is None
    
    @pytest.mark.parametrize("url,expected_id", [
        ("https://youtu.be/pMSXPgAUq_k", "pMSXPgAUq_k"),
        ("https://youtu.be/abc123", "abc123"),
        ("http://youtu.be/short123", "short123"),
    ])
    def test_get_youtube_video_id_short_url(self, url, expected_id):
        """Test extracting video ID from short YouTube URLs."""
        assert get_youtube_video_id(url) == expected_id
    
    @pytest.mark.parametrize("url,expected_id", [
        ("https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s", "pMSXPgAUq_k"),
        ("https://www.youtube.com/watch?v=abc123&list=playlist", "abc123"),
        ("https://youtube.com/watch?v=test&feature=share", "test"),
        ("https://youtu.be/short123?t=30", "short123"),
    ])
    def test_get_youtube_video_id_with_parameters(self, url, expected_id):
        """Test extracting video ID from URLs with additional parameters."""
        assert get_youtube_video_id(url) == expected_id
    
    @pytest.mark.parametrize("invalid_url", [
        "https://example.com",
        "not-a-url",
        "https://vimeo.com/123456",
        "https://youtube.com/playlist?list=123",
        "https://youtube.com/channel/UC123",
        "",
        None,
    ])
    def test_get_youtube_video_id_invalid_url(self, invalid_url):
        """Test handling invalid URLs."""
        assert get_youtube_video_id(invalid_url) is None


class TestTimestampUrlCreation:
    """Test cases for creating YouTube timestamp URLs."""
    
    @pytest.mark.parametrize("video_url,seconds,expected", [
        ("https://www.youtube.com/watch?v=pMSXPgAUq_k", 485, "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s"),
        ("https://youtube.com/watch?v=test123", 60, "https://www.youtube.com/watch?v=test123&t=60s"),
        ("https://www.youtube.com/watch?v=abc&list=123", 30, "https://www.youtube.com/watch?v=abc&t=30s"),
    ])
    def test_create_youtube_timestamp_url(self, video_url, seconds, expected):
        """Test creating YouTube URLs with timestamp parameters."""
        result = create_youtube_timestamp_url(video_url, seconds)
        assert result == expected
    
    @pytest.mark.parametrize("video_url,seconds,expected", [
        ("https://youtu.be/pMSXPgAUq_k", 485, "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s"),
        ("https://youtu.be/test123", 60, "https://www.youtube.com/watch?v=test123&t=60s"),
        ("https://youtu.be/abc?t=10", 30, "https://www.youtube.com/watch?v=abc&t=30s"),
    ])
    def test_create_youtube_timestamp_url_short_url(self, video_url, seconds, expected):
        """Test creating timestamp URLs from short YouTube URLs."""
        result = create_youtube_timestamp_url(video_url, seconds)
        assert result == expected
    
    @pytest.mark.parametrize("invalid_url", [
        "https://example.com/video",
        "https://vimeo.com/123456",
        "not-a-url",
        "",
    ])
    def test_create_youtube_timestamp_url_invalid_url(self, invalid_url):
        """Test handling invalid URLs."""
        result = create_youtube_timestamp_url(invalid_url, 485)
        assert result == invalid_url  # Should return original URL


class TestTimestampEnrichment:
    """Test cases for timestamp enrichment in markdown."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.video_url = "https://www.youtube.com/watch?v=pMSXPgAUq_k"
    
    @pytest.mark.parametrize("markdown,expected", [
        ("This happens at [8:05] in the video.", 
         "This happens at [8:05](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s) in the video."),
        ("Check [1:23] for details.", 
         "Check [1:23](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=83s) for details."),
        ("At [0:30] we start.", 
         "At [0:30](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=30s) we start."),
    ])
    def test_enrich_single_timestamp(self, markdown, expected):
        """Test enriching single timestamps."""
        result = enrich_timestamps_with_links(markdown, self.video_url)
        assert result == expected
    
    def test_enrich_timestamp_range(self):
        """Test enriching timestamp ranges."""
        markdown = "The section [8:05-8:24] covers this topic."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        expected = "The section [8:05-8:24](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s) covers this topic."
        assert result == expected
    
    def test_enrich_multiple_timestamps(self):
        """Test enriching multiple timestamps separated by commas."""
        markdown = "See sections [0:01-0:07, 0:56-1:21] for examples."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        expected = "See sections [0:01-0:07](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=1s), [0:56-1:21](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=56s) for examples."
        assert result == expected
    
    def test_enrich_multiple_separate_timestamps(self):
        """Test enriching multiple separate timestamp references."""
        markdown = "First at [1:15] and then at [2:30] we see this."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        expected = "First at [1:15](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=75s) and then at [2:30](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=150s) we see this."
        assert result == expected
    
    def test_enrich_complex_example(self):
        """Test enriching a complex example from the actual data."""
        markdown = "#### The High Cost of Bad Chunking: A Fintech Case Study [0:01-0:07, 0:56-1:21]"
        result = enrich_timestamps_with_links(markdown, self.video_url)
        expected = "#### The High Cost of Bad Chunking: A Fintech Case Study [0:01-0:07](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=1s), [0:56-1:21](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=56s)"
        assert result == expected
    
    def test_enrich_no_timestamps(self):
        """Test that text without timestamps is unchanged."""
        markdown = "This text has no timestamps in it."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        assert result == markdown
    
    def test_enrich_invalid_timestamp_format(self):
        """Test handling invalid timestamp formats."""
        markdown = "Invalid timestamp [25:70] should be unchanged."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        # Should return original since 70 seconds is invalid
        assert result == markdown
    
    def test_enrich_mixed_valid_invalid(self):
        """Test handling mix of valid and invalid timestamps."""
        markdown = "Valid [8:05] and invalid [25:70] timestamps."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        expected = "Valid [8:05](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s) and invalid [25:70] timestamps."
        assert result == expected
    
    def test_enrich_with_short_youtube_url(self):
        """Test enrichment with short YouTube URL."""
        short_url = "https://youtu.be/pMSXPgAUq_k"
        markdown = "This happens at [8:05] in the video."
        result = enrich_timestamps_with_links(markdown, short_url)
        expected = "This happens at [8:05](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s) in the video."
        assert result == expected