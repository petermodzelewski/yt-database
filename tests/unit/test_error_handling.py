"""
Tests for error handling and edge cases across the application.
"""

import pytest
from unittest.mock import Mock, patch
from notion_client.errors import APIResponseError
from youtube_notion.utils.markdown_converter import markdown_to_notion_blocks, enrich_timestamps_with_links
from youtube_notion.notion_db.operations import add_youtube_entry, find_database_by_name


class TestErrorHandling:
    """Test cases for error handling scenarios."""
    
    def test_markdown_converter_with_malformed_input(self):
        """Test markdown converter with malformed input."""
        # Test with None input - should raise AttributeError
        with pytest.raises(AttributeError):
            markdown_to_notion_blocks(None)
        
        # Test with empty string
        result = markdown_to_notion_blocks("")
        assert result == []
        
        # Test with only whitespace
        result = markdown_to_notion_blocks("   \n\n   ")
        assert result == []
    
    def test_timestamp_enrichment_with_invalid_video_url(self):
        """Test timestamp enrichment with invalid video URLs."""
        markdown = "Check [8:05] for details."
        
        # Test with invalid URL - the function still creates a link with the invalid URL
        result = enrich_timestamps_with_links(markdown, "not-a-url")
        expected = "Check [8:05](not-a-url) for details."
        assert result == expected
        
        # Test with None URL - the function handles this gracefully
        result = enrich_timestamps_with_links(markdown, None)
        expected = "Check [8:05](None) for details."
        assert result == expected
        
        # Test with empty URL
        result = enrich_timestamps_with_links(markdown, "")
        expected = "Check [8:05]() for details."
        assert result == expected
    
    def test_notion_api_errors(self):
        """Test handling of various Notion API errors."""
        mock_notion = Mock()
        
        # Test API response error - the function catches exceptions and returns None
        mock_notion.pages.create.side_effect = APIResponseError(
            response=Mock(status_code=400, text="Bad Request"),
            message="Invalid request",
            code="validation_error"
        )
        
        result = add_youtube_entry(
            mock_notion, "db-id", "title", "summary", 
            "https://youtube.com/watch?v=test", "channel", "cover"
        )
        
        # Function should return None when an error occurs
        assert result is None
    
    def test_notion_search_errors(self):
        """Test handling of Notion search errors."""
        mock_notion = Mock()
        
        # Test search API error - the function catches exceptions and returns None
        mock_notion.search.side_effect = APIResponseError(
            response=Mock(status_code=403, text="Forbidden"),
            message="Access denied",
            code="unauthorized"
        )
        
        result = find_database_by_name(mock_notion, "DB Name", "Page Name")
        
        # Function should return None when an error occurs
        assert result is None
    
    def test_large_content_handling(self):
        """Test handling of very large content."""
        # Create a very long markdown string
        large_markdown = "# Title\n\n" + "This is a very long paragraph. " * 1000
        
        # Should not crash
        blocks = markdown_to_notion_blocks(large_markdown)
        assert len(blocks) >= 2  # At least title and paragraph
        assert blocks[0]["type"] == "heading_1"
        assert blocks[1]["type"] == "paragraph"
    
    def test_special_characters_in_content(self):
        """Test handling of special characters in content."""
        markdown_with_special_chars = """# Title with émojis 🎉
        
This has **special** chars: àáâãäåæçèéêë & symbols: @#$%^&*()
        
- Bullet with 中文字符
- Another with русский текст"""
        
        blocks = markdown_to_notion_blocks(markdown_with_special_chars)
        assert len(blocks) >= 3  # Title, paragraph, and bullets
        
        # Verify special characters are preserved
        title_content = blocks[0]["heading_1"]["rich_text"][0]["text"]["content"]
        assert "émojis 🎉" in title_content
    
    @pytest.mark.parametrize("malformed_timestamp", [
        "[8:05",  # Missing closing bracket
        "8:05]",  # Missing opening bracket
        "[8:05-]",  # Incomplete range
        "[-8:05]",  # Invalid range start
        "[8:05-8:04]",  # End before start
        "[25:70]",  # Invalid seconds
        "[8:99]",  # Invalid seconds
    ])
    def test_malformed_timestamps(self, malformed_timestamp):
        """Test handling of malformed timestamps."""
        markdown = f"Check {malformed_timestamp} for details."
        video_url = "https://youtube.com/watch?v=test"
        
        # Should not crash and should leave malformed timestamps unchanged
        result = enrich_timestamps_with_links(markdown, video_url)
        assert malformed_timestamp in result
    
    def test_network_timeout_simulation(self):
        """Test handling of network timeouts."""
        mock_notion = Mock()
        mock_notion.pages.create.side_effect = TimeoutError("Request timed out")
        
        result = add_youtube_entry(
            mock_notion, "db-id", "title", "summary",
            "https://youtube.com/watch?v=test", "channel", "cover"
        )
        
        # Function should return None when a timeout occurs
        assert result is None
    
    def test_empty_database_results(self):
        """Test handling when database search returns empty results."""
        mock_notion = Mock()
        mock_notion.search.return_value = {"results": []}
        
        result = find_database_by_name(mock_notion, "Nonexistent DB", "Nonexistent Page")
        assert result is None
    
    def test_malformed_api_responses(self):
        """Test handling of malformed API responses."""
        mock_notion = Mock()
        
        # Test malformed search response
        mock_notion.search.return_value = {"results": [{"invalid": "structure"}]}
        
        # Should handle gracefully
        result = find_database_by_name(mock_notion, "DB Name", "Page Name")
        assert result is None
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_unicode_encoding_edge_cases(self, mock_get):
        """Test handling of unicode encoding edge cases in web scraping."""
        from src.youtube_notion.extractors.video_metadata_extractor import VideoMetadataExtractor
        
        extractor = VideoMetadataExtractor(youtube_api_key=None)
        
        # Test with completely malformed JSON
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"title":"Broken JSON \\u201","ownerChannelName":"Test"}'
        mock_get.return_value = mock_response
        
        # Should handle gracefully and fall back to raw strings
        result = extractor._get_metadata_via_scraping("dQw4w9WgXcQ")
        assert "Broken JSON" in result['title']
        assert result['channel'] == "Test"
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_unicode_encoding_empty_strings(self, mock_get):
        """Test handling of empty strings in unicode encoding."""
        from src.youtube_notion.extractors.video_metadata_extractor import VideoMetadataExtractor
        
        extractor = VideoMetadataExtractor(youtube_api_key=None)
        
        # Test with empty title and channel
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"title":"","ownerChannelName":""}'
        mock_get.return_value = mock_response
        
        # Should handle empty strings gracefully by falling back to defaults
        result = extractor._get_metadata_via_scraping("dQw4w9WgXcQ")
        assert result['title'] == "Unknown Title"  # Falls back to default when empty
        assert result['channel'] == "Unknown Channel"  # Falls back to default when empty
    
    @patch('src.youtube_notion.extractors.video_metadata_extractor.requests.get')
    def test_unicode_encoding_null_values(self, mock_get):
        """Test handling of null/None values in unicode encoding."""
        from src.youtube_notion.extractors.video_metadata_extractor import VideoMetadataExtractor
        
        extractor = VideoMetadataExtractor(youtube_api_key=None)
        
        # Test with HTML that doesn't contain title/channel patterns
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = 'var someOtherData = {"unrelated": "data"};'
        mock_get.return_value = mock_response
        
        # Should handle missing patterns gracefully
        result = extractor._get_metadata_via_scraping("dQw4w9WgXcQ")
        assert result['title'] == "Unknown Title"
        assert result['channel'] == "Unknown Channel"