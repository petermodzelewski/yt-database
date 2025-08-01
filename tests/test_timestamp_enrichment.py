"""
Unit tests for timestamp enrichment functionality.
Tests the conversion of timestamps to YouTube links.
"""

import unittest
from youtube_notion.utils.markdown_converter import (
    parse_timestamp_to_seconds,
    get_youtube_video_id,
    create_youtube_timestamp_url,
    enrich_timestamps_with_links
)


class TestTimestampParsing(unittest.TestCase):
    """Test cases for timestamp parsing functions."""
    
    def test_parse_timestamp_minutes_seconds(self):
        """Test parsing MM:SS format."""
        self.assertEqual(parse_timestamp_to_seconds("8:05"), 485)
        self.assertEqual(parse_timestamp_to_seconds("1:23"), 83)
        self.assertEqual(parse_timestamp_to_seconds("0:30"), 30)
        self.assertEqual(parse_timestamp_to_seconds("10:00"), 600)
    
    def test_parse_timestamp_hours_minutes_seconds(self):
        """Test parsing HH:MM:SS format."""
        self.assertEqual(parse_timestamp_to_seconds("1:23:45"), 5025)
        self.assertEqual(parse_timestamp_to_seconds("0:08:05"), 485)
        self.assertEqual(parse_timestamp_to_seconds("2:00:00"), 7200)
    
    def test_parse_timestamp_invalid_format(self):
        """Test parsing invalid timestamp formats."""
        with self.assertRaises(ValueError):
            parse_timestamp_to_seconds("8")
        with self.assertRaises(ValueError):
            parse_timestamp_to_seconds("8:05:30:15")
        with self.assertRaises(ValueError):
            parse_timestamp_to_seconds("invalid")


class TestYouTubeUrlParsing(unittest.TestCase):
    """Test cases for YouTube URL parsing."""
    
    def test_get_youtube_video_id_standard_url(self):
        """Test extracting video ID from standard YouTube URLs."""
        url = "https://www.youtube.com/watch?v=pMSXPgAUq_k"
        self.assertEqual(get_youtube_video_id(url), "pMSXPgAUq_k")
        
        url = "https://youtube.com/watch?v=abc123"
        self.assertEqual(get_youtube_video_id(url), "abc123")
    
    def test_get_youtube_video_id_short_url(self):
        """Test extracting video ID from short YouTube URLs."""
        url = "https://youtu.be/pMSXPgAUq_k"
        self.assertEqual(get_youtube_video_id(url), "pMSXPgAUq_k")
        
        url = "https://youtu.be/abc123"
        self.assertEqual(get_youtube_video_id(url), "abc123")
    
    def test_get_youtube_video_id_with_parameters(self):
        """Test extracting video ID from URLs with additional parameters."""
        url = "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s"
        self.assertEqual(get_youtube_video_id(url), "pMSXPgAUq_k")
        
        url = "https://www.youtube.com/watch?v=abc123&list=playlist"
        self.assertEqual(get_youtube_video_id(url), "abc123")
    
    def test_get_youtube_video_id_invalid_url(self):
        """Test handling invalid URLs."""
        self.assertIsNone(get_youtube_video_id("https://example.com"))
        self.assertIsNone(get_youtube_video_id("not-a-url"))
        self.assertIsNone(get_youtube_video_id("https://vimeo.com/123456"))


class TestTimestampUrlCreation(unittest.TestCase):
    """Test cases for creating YouTube timestamp URLs."""
    
    def test_create_youtube_timestamp_url(self):
        """Test creating YouTube URLs with timestamp parameters."""
        video_url = "https://www.youtube.com/watch?v=pMSXPgAUq_k"
        result = create_youtube_timestamp_url(video_url, 485)
        expected = "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s"
        self.assertEqual(result, expected)
    
    def test_create_youtube_timestamp_url_short_url(self):
        """Test creating timestamp URLs from short YouTube URLs."""
        video_url = "https://youtu.be/pMSXPgAUq_k"
        result = create_youtube_timestamp_url(video_url, 485)
        expected = "https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s"
        self.assertEqual(result, expected)
    
    def test_create_youtube_timestamp_url_invalid_url(self):
        """Test handling invalid URLs."""
        video_url = "https://example.com/video"
        result = create_youtube_timestamp_url(video_url, 485)
        self.assertEqual(result, video_url)  # Should return original URL


class TestTimestampEnrichment(unittest.TestCase):
    """Test cases for timestamp enrichment in markdown."""
    
    def setUp(self):
        self.video_url = "https://www.youtube.com/watch?v=pMSXPgAUq_k"
    
    def test_enrich_single_timestamp(self):
        """Test enriching single timestamps."""
        markdown = "This happens at [8:05] in the video."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        expected = "This happens at [8:05](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s) in the video."
        self.assertEqual(result, expected)
    
    def test_enrich_timestamp_range(self):
        """Test enriching timestamp ranges."""
        markdown = "The section [8:05-8:24] covers this topic."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        expected = "The section [8:05-8:24](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s) covers this topic."
        self.assertEqual(result, expected)
    
    def test_enrich_multiple_timestamps(self):
        """Test enriching multiple timestamps separated by commas."""
        markdown = "See sections [0:01-0:07, 0:56-1:21] for examples."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        expected = "See sections [0:01-0:07](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=1s), [0:56-1:21](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=56s) for examples."
        self.assertEqual(result, expected)
    
    def test_enrich_multiple_separate_timestamps(self):
        """Test enriching multiple separate timestamp references."""
        markdown = "First at [1:15] and then at [2:30] we see this."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        expected = "First at [1:15](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=75s) and then at [2:30](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=150s) we see this."
        self.assertEqual(result, expected)
    
    def test_enrich_complex_example(self):
        """Test enriching a complex example from the actual data."""
        markdown = "#### The High Cost of Bad Chunking: A Fintech Case Study [0:01-0:07, 0:56-1:21]"
        result = enrich_timestamps_with_links(markdown, self.video_url)
        expected = "#### The High Cost of Bad Chunking: A Fintech Case Study [0:01-0:07](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=1s), [0:56-1:21](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=56s)"
        self.assertEqual(result, expected)
    
    def test_enrich_no_timestamps(self):
        """Test that text without timestamps is unchanged."""
        markdown = "This text has no timestamps in it."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        self.assertEqual(result, markdown)
    
    def test_enrich_invalid_timestamp_format(self):
        """Test handling invalid timestamp formats."""
        markdown = "Invalid timestamp [25:70] should be unchanged."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        # Should return original since 70 seconds is invalid
        self.assertEqual(result, markdown)
    
    def test_enrich_mixed_valid_invalid(self):
        """Test handling mix of valid and invalid timestamps."""
        markdown = "Valid [8:05] and invalid [25:70] timestamps."
        result = enrich_timestamps_with_links(markdown, self.video_url)
        expected = "Valid [8:05](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s) and invalid [25:70] timestamps."
        self.assertEqual(result, expected)
    
    def test_enrich_with_short_youtube_url(self):
        """Test enrichment with short YouTube URL."""
        short_url = "https://youtu.be/pMSXPgAUq_k"
        markdown = "This happens at [8:05] in the video."
        result = enrich_timestamps_with_links(markdown, short_url)
        expected = "This happens at [8:05](https://www.youtube.com/watch?v=pMSXPgAUq_k&t=485s) in the video."
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()