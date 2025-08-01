"""
Tests for the main application entry point.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from youtube_notion.main import main


class TestMain:
    """Test cases for main application function."""
    
    @patch('youtube_notion.main.Client')
    @patch('youtube_notion.main.find_database_by_name')
    @patch('youtube_notion.main.add_youtube_entry')
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test-token'})
    def test_main_success_flow(self, mock_add_entry, mock_find_db, mock_client_class):
        """Test successful execution of main function."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_find_db.return_value = "test-db-id"
        mock_add_entry.return_value = "test-page-id"
        
        # Capture print output
        with patch('builtins.print') as mock_print:
            main()
        
        # Verify calls (load_dotenv is called at module level, not in main)
        mock_client_class.assert_called_once_with(auth='test-token')
        mock_find_db.assert_called_once_with(mock_client, "YT Summaries", "YouTube Knowledge Base")
        mock_add_entry.assert_called_once()
        
        # Verify success message
        mock_print.assert_called_with("Entry added successfully with ID: test-page-id")
    
    @patch.dict(os.environ, {}, clear=True)
    def test_main_missing_token(self):
        """Test main function with missing NOTION_TOKEN."""
        with patch('builtins.print') as mock_print:
            main()
        
        mock_print.assert_called_with("Error: NOTION_TOKEN environment variable not set")
    
    @patch('youtube_notion.main.Client')
    @patch('youtube_notion.main.find_database_by_name')
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test-token'})
    def test_main_database_not_found(self, mock_find_db, mock_client_class):
        """Test main function when database is not found."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_find_db.return_value = None
        
        with patch('builtins.print') as mock_print:
            main()
        
        mock_print.assert_called_with("Error: Could not find 'YT Summaries' database in 'YouTube Knowledge Base' page")
    
    @patch('youtube_notion.main.Client')
    @patch('youtube_notion.main.find_database_by_name')
    @patch('youtube_notion.main.add_youtube_entry')
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test-token'})
    def test_main_add_entry_failure(self, mock_add_entry, mock_find_db, mock_client_class):
        """Test main function when adding entry fails."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_find_db.return_value = "test-db-id"
        mock_add_entry.return_value = None
        
        with patch('builtins.print') as mock_print:
            main()
        
        mock_print.assert_called_with("Failed to add entry")
    
    @patch('youtube_notion.main.Client')
    @patch('youtube_notion.main.find_database_by_name')
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test-token'})
    def test_main_notion_client_exception(self, mock_find_db, mock_client_class):
        """Test main function when Notion client raises exception."""
        # Setup mocks to raise exception
        mock_client_class.side_effect = Exception("API Error")
        
        # Should not crash, but will raise exception
        with pytest.raises(Exception, match="API Error"):
            main()