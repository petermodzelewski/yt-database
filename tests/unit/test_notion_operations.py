"""
Tests for Notion database operations.
"""

import pytest
from unittest.mock import Mock, patch
from youtube_notion.notion_db.operations import add_youtube_entry, find_database_by_name


class TestAddYouTubeEntry:
    """Test cases for add_youtube_entry function."""
    
    def test_youtube_entry_block_structure(self, sample_video_data):
        """Test that YouTube entry creates correct block structure."""
        # Mock Notion client
        mock_notion = Mock()
        mock_page = {"id": "test-page-id"}
        mock_notion.pages.create.return_value = mock_page
        
        # Call the function
        result = add_youtube_entry(
            mock_notion, 
            "test-db-id", 
            sample_video_data["Title"], 
            sample_video_data["Summary"], 
            sample_video_data["Video URL"], 
            sample_video_data["Channel"], 
            sample_video_data["Cover"]
        )
        
        # Verify the function returned the page ID
        assert result == "test-page-id"
        
        # Verify pages.create was called
        mock_notion.pages.create.assert_called_once()
        
        # Get the call arguments
        call_args = mock_notion.pages.create.call_args
        
        # Verify the children (blocks) structure
        children = call_args.kwargs['children']
        
        # Should have at least 3 blocks: embed, divider, and summary content
        assert len(children) >= 3
        
        # First block should be YouTube embed
        first_block = children[0]
        assert first_block['type'] == 'embed'
        assert first_block['embed']['url'] == sample_video_data["Video URL"]
        
        # Second block should be divider
        second_block = children[1]
        assert second_block['type'] == 'divider'
        
        # Third block should be from the summary (heading_1)
        third_block = children[2]
        assert third_block['type'] == 'heading_1'
        assert third_block['heading_1']['rich_text'][0]['text']['content'] == 'Test Summary'
        
        # Verify properties
        properties = call_args.kwargs['properties']
        assert properties['Title']['title'][0]['text']['content'] == sample_video_data["Title"]
        assert properties['Video URL']['url'] == sample_video_data["Video URL"]
        assert properties['Channel']['rich_text'][0]['text']['content'] == sample_video_data["Channel"]
        
        # Verify cover
        cover = call_args.kwargs['cover']
        assert cover['type'] == 'external'
        assert cover['external']['url'] == sample_video_data["Cover"]
    
    def test_add_youtube_entry_api_error(self, sample_video_data):
        """Test handling of Notion API errors."""
        mock_notion = Mock()
        mock_notion.pages.create.side_effect = Exception("API Error")
        
        result = add_youtube_entry(
            mock_notion, 
            "test-db-id", 
            sample_video_data["Title"], 
            sample_video_data["Summary"], 
            sample_video_data["Video URL"], 
            sample_video_data["Channel"], 
            sample_video_data["Cover"]
        )
        
        # Function should return None when an error occurs
        assert result is None
    
    def test_add_youtube_entry_empty_summary(self, sample_video_data):
        """Test handling of empty summary."""
        mock_notion = Mock()
        mock_notion.pages.create.return_value = {"id": "test-page-id"}
        
        result = add_youtube_entry(
            mock_notion, 
            "test-db-id", 
            sample_video_data["Title"], 
            "", 
            sample_video_data["Video URL"], 
            sample_video_data["Channel"], 
            sample_video_data["Cover"]
        )
        
        assert result == "test-page-id"
        
        # Verify that even with empty summary, embed and divider are still added
        call_args = mock_notion.pages.create.call_args
        children = call_args.kwargs['children']
        assert len(children) >= 2  # At least embed and divider


class TestFindDatabaseByName:
    """Test cases for find_database_by_name function."""
    
    def test_find_database_success(self):
        """Test successful database finding."""
        mock_notion = Mock()
        mock_notion.search.return_value = {
            "results": [
                {
                    "id": "test-db-id",
                    "object": "database",
                    "title": [{"plain_text": "YT Summaries"}],
                    "parent": {"page_id": "page-id"}
                }
            ]
        }
        
        # Mock the page retrieval for parent check
        mock_notion.pages.retrieve.return_value = {
            "properties": {
                "title": {
                    "title": [{"plain_text": "YouTube Knowledge Base"}]
                }
            }
        }
        
        result = find_database_by_name(mock_notion, "YT Summaries", "YouTube Knowledge Base")
        
        assert result == "test-db-id"
        mock_notion.search.assert_called_once()
    
    def test_find_database_page_not_found(self):
        """Test when parent page is not found."""
        mock_notion = Mock()
        mock_notion.search.return_value = {"results": []}
        
        result = find_database_by_name(mock_notion, "YT Summaries", "YouTube Knowledge Base")
        
        assert result is None
        mock_notion.search.assert_called_once()
    
    def test_find_database_db_not_found(self):
        """Test when database is not found in parent page."""
        mock_notion = Mock()
        mock_notion.search.return_value = {
            "results": [
                {
                    "id": "page-id",
                    "object": "page",
                    "properties": {
                        "title": {
                            "title": [{"text": {"content": "YouTube Knowledge Base"}}]
                        }
                    }
                }
            ]
        }
        
        # Mock empty database list
        mock_notion.databases.list.return_value = {"results": []}
        
        result = find_database_by_name(mock_notion, "YT Summaries", "YouTube Knowledge Base")
        
        assert result is None
    
    def test_find_database_api_error(self):
        """Test handling of API errors."""
        mock_notion = Mock()
        mock_notion.search.side_effect = Exception("API Error")
        
        result = find_database_by_name(mock_notion, "YT Summaries", "YouTube Knowledge Base")
        
        # Function should return None when an error occurs
        assert result is None