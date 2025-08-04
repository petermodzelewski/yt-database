#!/usr/bin/env python3
"""
Integration tests for main.py YouTube integration functionality.
Tests the complete application workflow including environment validation,
Notion client initialization, and YouTube video processing.
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, 'src')

from youtube_notion.main import (
    main, 
    load_application_config, 
    initialize_notion_client,
    find_notion_database,
    process_youtube_video,
    add_to_notion_database
)


class TestEnvironmentValidation:
    """Test environment variable validation functionality."""
    
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test_token'}, clear=True)
    def test_load_application_config_example_mode(self):
        """Test configuration loading for example data mode."""
        config = load_application_config(youtube_mode=False)
        assert config is not None
        assert config.notion.notion_token == 'test_token'
    
    @patch.dict(os.environ, {
        'NOTION_TOKEN': 'test_token',
        'GEMINI_API_KEY': 'test_gemini_key',
        'YOUTUBE_API_KEY': 'test_youtube_key'
    }, clear=True)
    def test_load_application_config_youtube_mode_complete(self):
        """Test configuration loading for YouTube mode with all keys."""
        config = load_application_config(youtube_mode=True)
        assert config is not None
        assert config.notion.notion_token == 'test_token'
        assert config.youtube_processor is not None
    
    @patch.dict(os.environ, {
        'NOTION_TOKEN': 'test_token',
        'GEMINI_API_KEY': 'test_gemini_key'
    }, clear=True)
    def test_load_application_config_youtube_mode_minimal(self):
        """Test configuration loading for YouTube mode with minimal keys."""
        config = load_application_config(youtube_mode=True)
        assert config is not None
        assert config.notion.notion_token == 'test_token'
        assert config.youtube_processor is not None
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('youtube_notion.config.settings.load_dotenv')
    def test_load_application_config_missing_notion_token(self, mock_load_dotenv):
        """Test configuration loading with missing NOTION_TOKEN."""
        mock_load_dotenv.return_value = None  # Prevent loading from .env file
        config = load_application_config(youtube_mode=False)
        assert config is None
    
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test_token'}, clear=True)
    @patch('youtube_notion.config.settings.load_dotenv')
    def test_load_application_config_missing_gemini_key(self, mock_load_dotenv):
        """Test configuration loading with missing GEMINI_API_KEY in YouTube mode."""
        mock_load_dotenv.return_value = None  # Prevent loading from .env file
        config = load_application_config(youtube_mode=True)
        assert config is None


class TestNotionClientInitialization:
    """Test Notion client initialization and database operations."""
    
    @patch('youtube_notion.main.Client')
    def test_initialize_notion_client_success(self, mock_client_class):
        """Test successful Notion client initialization."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        result = initialize_notion_client('test_token')
        
        assert result == mock_client
        mock_client_class.assert_called_once_with(auth='test_token')
        mock_client.users.me.assert_called_once()
    
    @patch('youtube_notion.main.Client')
    def test_initialize_notion_client_failure(self, mock_client_class):
        """Test Notion client initialization failure."""
        mock_client = MagicMock()
        mock_client.users.me.side_effect = Exception("Authentication failed")
        mock_client_class.return_value = mock_client
        
        result = initialize_notion_client('invalid_token')
        
        assert result is None
    
    @patch('youtube_notion.main.find_database_by_name')
    def test_find_notion_database_success(self, mock_find_db):
        """Test successful database finding."""
        mock_notion = MagicMock()
        mock_config = MagicMock()
        mock_config.notion.database_name = "YT Summaries"
        mock_config.notion.parent_page_name = "YouTube Knowledge Base"
        mock_find_db.return_value = "test_db_id"
        
        result = find_notion_database(mock_notion, mock_config)
        
        assert result == "test_db_id"
        mock_find_db.assert_called_once_with(mock_notion, "YT Summaries", "YouTube Knowledge Base")
    
    @patch('youtube_notion.main.find_database_by_name')
    def test_find_notion_database_not_found(self, mock_find_db):
        """Test database not found scenario."""
        mock_notion = MagicMock()
        mock_config = MagicMock()
        mock_config.notion.database_name = "YT Summaries"
        mock_config.notion.parent_page_name = "YouTube Knowledge Base"
        mock_find_db.return_value = None
        
        result = find_notion_database(mock_notion, mock_config)
        
        assert result is None
    
    @patch('youtube_notion.main.find_database_by_name')
    def test_find_notion_database_exception(self, mock_find_db):
        """Test database finding with exception."""
        mock_notion = MagicMock()
        mock_config = MagicMock()
        mock_config.notion.database_name = "YT Summaries"
        mock_config.notion.parent_page_name = "YouTube Knowledge Base"
        mock_find_db.side_effect = Exception("Database access error")
        
        result = find_notion_database(mock_notion, mock_config)
        
        assert result is None


class TestYouTubeVideoProcessing:
    """Test YouTube video processing functionality."""
    
    @patch('youtube_notion.processors.youtube_processor.YouTubeProcessor')
    def test_process_youtube_video_success(self, mock_processor_class):
        """Test successful YouTube video processing."""
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        mock_processor.validate_youtube_url.return_value = True
        mock_processor.process_video.return_value = {
            "Title": "Test Video",
            "Channel": "Test Channel",
            "Video URL": "https://www.youtube.com/watch?v=test123",
            "Cover": "https://img.youtube.com/vi/test123/maxresdefault.jpg",
            "Summary": "Test summary"
        }
        
        mock_config = MagicMock()
        mock_config.youtube_processor = MagicMock()
        mock_config.youtube_processor.gemini_api_key = 'test_gemini_key'
        mock_config.youtube_processor.youtube_api_key = 'test_youtube_key'
        
        result = process_youtube_video(
            "https://www.youtube.com/watch?v=test123",
            "Custom prompt",
            mock_config
        )
        
        assert result is not None
        assert result["Title"] == "Test Video"
        mock_processor_class.assert_called_once_with(mock_config.youtube_processor)
        mock_processor.validate_youtube_url.assert_called_once()
        mock_processor.process_video.assert_called_once_with(
            "https://www.youtube.com/watch?v=test123",
            "Custom prompt"
        )
    
    @patch('youtube_notion.processors.youtube_processor.YouTubeProcessor')
    def test_process_youtube_video_invalid_url(self, mock_processor_class):
        """Test YouTube video processing with invalid URL."""
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        mock_processor.validate_youtube_url.return_value = False
        
        env_vars = {'GEMINI_API_KEY': 'test_gemini_key'}
        
        result = process_youtube_video("invalid_url", None, env_vars)
        
        assert result is None
    
    @patch('youtube_notion.processors.youtube_processor.YouTubeProcessor')
    def test_process_youtube_video_processing_error(self, mock_processor_class):
        """Test YouTube video processing with processing error."""
        from youtube_notion.processors.exceptions import YouTubeProcessingError
        
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        mock_processor.validate_youtube_url.return_value = True
        mock_processor.process_video.side_effect = YouTubeProcessingError("Processing failed")
        
        env_vars = {'GEMINI_API_KEY': 'test_gemini_key'}
        
        result = process_youtube_video("https://www.youtube.com/watch?v=test123", None, env_vars)
        
        assert result is None
    
    def test_process_youtube_video_import_error(self):
        """Test YouTube video processing with import error."""
        env_vars = {'GEMINI_API_KEY': 'test_gemini_key'}
        
        # Mock the import to raise ImportError
        with patch('builtins.__import__', side_effect=ImportError("Module not found")):
            result = process_youtube_video("https://www.youtube.com/watch?v=test123", None, env_vars)
            assert result is None


class TestNotionDatabaseOperations:
    """Test Notion database operations."""
    
    @patch('youtube_notion.main.add_youtube_entry')
    def test_add_to_notion_database_success(self, mock_add_entry):
        """Test successful addition to Notion database."""
        mock_notion = MagicMock()
        mock_add_entry.return_value = "test_page_id"
        
        video_data = {
            "Title": "Test Video",
            "Summary": "Test summary",
            "Video URL": "https://www.youtube.com/watch?v=test123",
            "Channel": "Test Channel",
            "Cover": "https://img.youtube.com/vi/test123/maxresdefault.jpg"
        }
        
        result = add_to_notion_database(mock_notion, "test_db_id", video_data)
        
        assert result is True
        mock_add_entry.assert_called_once_with(
            mock_notion,
            "test_db_id",
            "Test Video",
            "Test summary",
            "https://www.youtube.com/watch?v=test123",
            "Test Channel",
            "https://img.youtube.com/vi/test123/maxresdefault.jpg"
        )
    
    @patch('youtube_notion.main.add_youtube_entry')
    def test_add_to_notion_database_failure(self, mock_add_entry):
        """Test failed addition to Notion database."""
        mock_notion = MagicMock()
        mock_add_entry.return_value = None
        
        video_data = {
            "Title": "Test Video",
            "Summary": "Test summary",
            "Video URL": "https://www.youtube.com/watch?v=test123",
            "Channel": "Test Channel",
            "Cover": "https://img.youtube.com/vi/test123/maxresdefault.jpg"
        }
        
        result = add_to_notion_database(mock_notion, "test_db_id", video_data)
        
        assert result is False
    
    @patch('youtube_notion.main.add_youtube_entry')
    def test_add_to_notion_database_exception(self, mock_add_entry):
        """Test addition to Notion database with exception."""
        mock_notion = MagicMock()
        mock_add_entry.side_effect = Exception("Database error")
        
        video_data = {
            "Title": "Test Video",
            "Summary": "Test summary",
            "Video URL": "https://www.youtube.com/watch?v=test123",
            "Channel": "Test Channel",
            "Cover": "https://img.youtube.com/vi/test123/maxresdefault.jpg"
        }
        
        result = add_to_notion_database(mock_notion, "test_db_id", video_data)
        
        assert result is False


class TestMainIntegrationWorkflow:
    """Test the complete main application workflow."""
    
    @patch('youtube_notion.main.Client')
    @patch('youtube_notion.main.find_database_by_name')
    @patch('youtube_notion.main.add_youtube_entry')
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test_token'}, clear=True)
    def test_main_example_data_mode_success(self, mock_add_entry, mock_find_db, mock_client_class):
        """Test complete workflow with example data mode."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_find_db.return_value = "test_db_id"
        mock_add_entry.return_value = "test_page_id"
        
        # Call main function
        result = main()
        
        # Verify success
        assert result is True
        
        # Verify calls
        mock_client_class.assert_called_once_with(auth='test_token')
        mock_client.users.me.assert_called_once()
        mock_find_db.assert_called_once_with(mock_client, "YT Summaries", "YouTube Knowledge Base")
        mock_add_entry.assert_called_once()
    
    @patch('youtube_notion.main.Client')
    @patch('youtube_notion.main.find_database_by_name')
    @patch('youtube_notion.main.add_youtube_entry')
    @patch('youtube_notion.processors.youtube_processor.YouTubeProcessor')
    @patch.dict(os.environ, {
        'NOTION_TOKEN': 'test_token',
        'GEMINI_API_KEY': 'test_gemini_key',
        'YOUTUBE_API_KEY': 'test_youtube_key'
    }, clear=True)
    def test_main_youtube_mode_success(self, mock_processor_class, mock_add_entry, mock_find_db, mock_client_class):
        """Test complete workflow with YouTube URL processing."""
        # Setup mocks
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_find_db.return_value = "test_db_id"
        mock_add_entry.return_value = "test_page_id"
        
        mock_processor = MagicMock()
        mock_processor_class.return_value = mock_processor
        mock_processor.validate_youtube_url.return_value = True
        mock_processor.process_video.return_value = {
            "Title": "Test Video Title",
            "Video URL": "https://www.youtube.com/watch?v=test123",
            "Channel": "Test Channel",
            "Cover": "https://img.youtube.com/vi/test123/maxresdefault.jpg",
            "Summary": "Test summary content"
        }
        
        # Call main function
        test_url = "https://www.youtube.com/watch?v=test123"
        test_prompt = "Custom test prompt"
        result = main(youtube_url=test_url, custom_prompt=test_prompt)
        
        # Verify success
        assert result is True
        
        # Verify processor calls - expect config object, not individual parameters
        assert mock_processor_class.call_count == 1
        call_args = mock_processor_class.call_args[0][0]  # Get the config object
        assert call_args.gemini_api_key == 'test_gemini_key'
        assert call_args.youtube_api_key == 'test_youtube_key'
        mock_processor.validate_youtube_url.assert_called_once_with(test_url)
        mock_processor.process_video.assert_called_once_with(test_url, test_prompt)
        
        # Verify Notion calls
        mock_client_class.assert_called_once_with(auth='test_token')
        mock_find_db.assert_called_once_with(mock_client, "YT Summaries", "YouTube Knowledge Base")
        mock_add_entry.assert_called_once_with(
            mock_client,
            "test_db_id",
            "Test Video Title",
            "Test summary content",
            "https://www.youtube.com/watch?v=test123",
            "Test Channel",
            "https://img.youtube.com/vi/test123/maxresdefault.jpg"
        )
    
    @patch.dict(os.environ, {}, clear=True)
    @patch('youtube_notion.config.settings.load_dotenv')
    def test_main_missing_environment_variables(self, mock_load_dotenv):
        """Test main function with missing environment variables."""
        mock_load_dotenv.return_value = None  # Prevent loading from .env file
        result = main()
        assert result is False  # Should return False, not raise SystemExit
    
    @patch('youtube_notion.main.Client')
    @patch.dict(os.environ, {'NOTION_TOKEN': 'invalid_token'}, clear=True)
    def test_main_notion_client_failure(self, mock_client_class):
        """Test main function with Notion client initialization failure."""
        mock_client = MagicMock()
        mock_client.users.me.side_effect = Exception("Authentication failed")
        mock_client_class.return_value = mock_client
        
        result = main()
        
        assert result is False
    
    @patch('youtube_notion.main.Client')
    @patch('youtube_notion.main.find_database_by_name')
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test_token'}, clear=True)
    def test_main_database_not_found(self, mock_find_db, mock_client_class):
        """Test main function with database not found."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_find_db.return_value = None
        
        result = main()
        
        assert result is False
    
    @patch('youtube_notion.main.Client')
    @patch('youtube_notion.main.find_database_by_name')
    @patch('youtube_notion.main.add_youtube_entry')
    @patch.dict(os.environ, {'NOTION_TOKEN': 'test_token'}, clear=True)
    def test_main_notion_entry_failure(self, mock_add_entry, mock_find_db, mock_client_class):
        """Test main function with Notion entry addition failure."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        mock_find_db.return_value = "test_db_id"
        mock_add_entry.return_value = None
        
        result = main()
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])