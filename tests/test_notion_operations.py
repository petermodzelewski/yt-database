"""
Tests for Notion database operations.
"""

import unittest
from unittest.mock import Mock, patch
from notion_db.operations import add_youtube_entry


class TestNotionOperations(unittest.TestCase):
    """Test cases for Notion database operations."""
    
    def test_youtube_entry_block_structure(self):
        """Test that YouTube entry creates correct block structure."""
        # Mock Notion client
        mock_notion = Mock()
        mock_page = {"id": "test-page-id"}
        mock_notion.pages.create.return_value = mock_page
        
        # Test data
        database_id = "test-db-id"
        title = "Test Video"
        summary = "# Test Summary\n\nThis is a test."
        video_url = "https://youtube.com/watch?v=test"
        channel = "Test Channel"
        cover_url = "https://example.com/cover.jpg"
        
        # Call the function
        result = add_youtube_entry(
            mock_notion, database_id, title, summary, 
            video_url, channel, cover_url
        )
        
        # Verify the function returned the page ID
        self.assertEqual(result, "test-page-id")
        
        # Verify pages.create was called
        mock_notion.pages.create.assert_called_once()
        
        # Get the call arguments
        call_args = mock_notion.pages.create.call_args
        
        # Verify the children (blocks) structure
        children = call_args.kwargs['children']
        
        # Should have at least 3 blocks: embed, divider, and summary content
        self.assertGreaterEqual(len(children), 3)
        
        # First block should be YouTube embed
        first_block = children[0]
        self.assertEqual(first_block['type'], 'embed')
        self.assertEqual(first_block['embed']['url'], video_url)
        
        # Second block should be divider
        second_block = children[1]
        self.assertEqual(second_block['type'], 'divider')
        
        # Third block should be from the summary (heading_1)
        third_block = children[2]
        self.assertEqual(third_block['type'], 'heading_1')
        self.assertEqual(
            third_block['heading_1']['rich_text'][0]['text']['content'], 
            'Test Summary'
        )
        
        # Verify properties
        properties = call_args.kwargs['properties']
        self.assertEqual(
            properties['Title']['title'][0]['text']['content'], 
            title
        )
        self.assertEqual(properties['Video URL']['url'], video_url)
        self.assertEqual(
            properties['Channel']['rich_text'][0]['text']['content'], 
            channel
        )
        
        # Verify cover
        cover = call_args.kwargs['cover']
        self.assertEqual(cover['type'], 'external')
        self.assertEqual(cover['external']['url'], cover_url)


if __name__ == '__main__':
    unittest.main()