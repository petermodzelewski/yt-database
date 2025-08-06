"""
Tests for the main application entry point.
Tests the basic functionality of the main function with example data mode.
For comprehensive integration tests, see test_main_youtube_integration.py.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os
from src.youtube_notion.main import main


class TestMain:
    """Test cases for main application function."""
    
    @patch('src.youtube_notion.main.Client')
    @patch('src.youtube_notion.main.find_database_by_name')
    @patch('src.youtube_notion.main.add_youtube_entry')
    @patch('src.youtube_notion.config.settings.load_dotenv')  # Mock dotenv loading
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test-token'}, clear=True)
    def test_main_success_flow(self, mock_dotenv, mock_add_entry, mock_find_db, mock_client_class):
        """Test successful execution of main function."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_find_db.return_value = "test-db-id"
        mock_add_entry.return_value = "test-page-id"
        
        # Call main function
        result = main()
        
        # Verify success
        assert result is True
        
        # Verify calls
        mock_client_class.assert_called_once_with(auth='test-token')
        mock_client.users.me.assert_called_once()  # Connection test
        mock_find_db.assert_called_once()
        mock_add_entry.assert_called_once()
    
    @patch('src.youtube_notion.config.settings.load_dotenv')  # Mock dotenv loading
    @patch.dict(os.environ, {}, clear=True)
    def test_main_missing_token(self, mock_dotenv):
        """Test main function with missing NOTION_TOKEN."""
        # Should return False (not exit) when configuration fails
        result = main()
        assert result is False
    
    @patch('src.youtube_notion.main.Client')
    @patch('src.youtube_notion.main.find_database_by_name')
    @patch('src.youtube_notion.config.settings.load_dotenv')  # Mock dotenv loading
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test-token'}, clear=True)
    def test_main_database_not_found(self, mock_dotenv, mock_find_db, mock_client_class):
        """Test main function when database is not found."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_find_db.return_value = None
        
        result = main()
        
        # Should return False for failure
        assert result is False
    
    @patch('src.youtube_notion.main.Client')
    @patch('src.youtube_notion.main.find_database_by_name')
    @patch('src.youtube_notion.main.add_youtube_entry')
    @patch('src.youtube_notion.config.settings.load_dotenv')  # Mock dotenv loading
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test-token'}, clear=True)
    def test_main_add_entry_failure(self, mock_dotenv, mock_add_entry, mock_find_db, mock_client_class):
        """Test main function when adding entry fails."""
        # Setup mocks
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_find_db.return_value = "test-db-id"
        mock_add_entry.return_value = None
        
        result = main()
        
        # Should return False for failure
        assert result is False
    
    @patch('src.youtube_notion.main.Client')
    @patch('src.youtube_notion.main.find_database_by_name')
    @patch('src.youtube_notion.config.settings.load_dotenv')  # Mock dotenv loading
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test-token'}, clear=True)
    def test_main_notion_client_exception(self, mock_dotenv, mock_find_db, mock_client_class):
        """Test main function when Notion client raises exception."""
        # Setup mocks to raise exception during connection test
        mock_client = Mock()
        mock_client.users.me.side_effect = Exception("API Error")
        mock_client_class.return_value = mock_client
        
        result = main()
        
        # Should return False for failure (not raise exception)
        assert result is False