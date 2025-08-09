#!/usr/bin/env python3
"""
Tests for main.py functions including UI mode functionality.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock, Mock
from io import StringIO
import time

# Add src to path for imports
sys.path.insert(0, 'src')

from src.youtube_notion.main import main_ui, load_application_config
from src.youtube_notion.utils.exceptions import ConfigurationError


class TestMainUI:
    """Test main_ui function for web UI mode."""
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    @patch('src.youtube_notion.main.VideoProcessor')
    @patch('src.youtube_notion.main.QueueManager')
    @patch('src.youtube_notion.main.WebServerConfig')
    @patch('src.youtube_notion.main.WebServer')
    @patch('webbrowser.open')
    @patch('time.sleep')
    def test_main_ui_success(self, mock_sleep, mock_browser, mock_web_server_class, 
                           mock_web_config_class, mock_queue_manager_class, 
                           mock_video_processor_class, mock_factory_class, 
                           mock_load_config):
        """Test successful UI mode initialization and startup."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_metadata_extractor = Mock()
        mock_summary_writer = Mock()
        mock_storage = Mock()
        mock_factory.create_all_components.return_value = (mock_metadata_extractor, mock_summary_writer, mock_storage)
        
        mock_processor = Mock()
        mock_video_processor_class.return_value = mock_processor
        
        mock_queue_manager = Mock()
        mock_queue_manager_class.return_value = mock_queue_manager
        
        mock_web_config = Mock()
        mock_web_config.host = "127.0.0.1"
        mock_web_config.port = 8080
        mock_web_config_class.from_env.return_value = mock_web_config
        
        mock_web_server = Mock()
        mock_web_server.is_running = False  # Don't enter the loop
        mock_web_server_class.return_value = mock_web_server
        
        # Test
        result = main_ui()
        
        # Assertions
        assert result is True
        mock_load_config.assert_called_once_with(youtube_mode=True)
        mock_factory_class.assert_called_once_with(mock_config)
        mock_factory.create_all_components.assert_called_once()
        mock_video_processor_class.assert_called_once_with(mock_metadata_extractor, mock_summary_writer, mock_storage)
        mock_processor.validate_configuration.assert_called_once()
        mock_queue_manager_class.assert_called_once_with(mock_processor)
        mock_web_config_class.from_env.assert_called_once()
        mock_web_server_class.assert_called_once_with(mock_queue_manager, mock_web_config)
        mock_queue_manager.start_processing.assert_called_once()
        mock_web_server.start.assert_called_once()
        mock_browser.assert_called_once_with("http://127.0.0.1:8080")
        mock_web_server.stop.assert_called_once()
        mock_queue_manager.stop_processing.assert_called_once()
    
    @patch('src.youtube_notion.main.load_application_config')
    def test_main_ui_configuration_failure(self, mock_load_config):
        """Test UI mode failure when configuration is invalid."""
        mock_load_config.return_value = None
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main_ui()
        
        assert result is False
        output = mock_stdout.getvalue()
        assert "Configuration validation failed" in output
        assert "Web UI mode requires valid API keys" in output
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    def test_main_ui_configuration_error_exception(self, mock_factory_class, mock_load_config):
        """Test UI mode handles ConfigurationError exceptions."""
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_factory_class.side_effect = ConfigurationError("Test config error", details="Test details")
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main_ui()
        
        assert result is False
        output = mock_stdout.getvalue()
        assert "Configuration error - Test config error" in output
        assert "Details: Test details" in output
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    def test_main_ui_import_error(self, mock_factory_class, mock_load_config):
        """Test UI mode handles ImportError exceptions."""
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_factory_class.side_effect = ImportError("Missing fastapi")
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main_ui()
        
        assert result is False
        output = mock_stdout.getvalue()
        assert "Failed to import required web components" in output
        assert "pip install fastapi uvicorn pydantic" in output
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    def test_main_ui_unexpected_error(self, mock_factory_class, mock_load_config):
        """Test UI mode handles unexpected exceptions."""
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_factory_class.side_effect = Exception("Unexpected error")
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main_ui()
        
        assert result is False
        output = mock_stdout.getvalue()
        assert "Unexpected error during web UI startup" in output
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    @patch('src.youtube_notion.main.VideoProcessor')
    @patch('src.youtube_notion.main.QueueManager')
    @patch('src.youtube_notion.main.WebServerConfig')
    @patch('src.youtube_notion.main.WebServer')
    @patch('webbrowser.open')
    @patch('time.sleep')
    def test_main_ui_browser_open_failure(self, mock_sleep, mock_browser, mock_web_server_class, 
                                        mock_web_config_class, mock_queue_manager_class, 
                                        mock_video_processor_class, mock_factory_class, 
                                        mock_load_config):
        """Test UI mode handles browser opening failure gracefully."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_metadata_extractor = Mock()
        mock_summary_writer = Mock()
        mock_storage = Mock()
        mock_factory.create_all_components.return_value = (mock_metadata_extractor, mock_summary_writer, mock_storage)
        
        mock_processor = Mock()
        mock_video_processor_class.return_value = mock_processor
        
        mock_queue_manager = Mock()
        mock_queue_manager_class.return_value = mock_queue_manager
        
        mock_web_config = Mock()
        mock_web_config.host = "127.0.0.1"
        mock_web_config.port = 8080
        mock_web_config_class.from_env.return_value = mock_web_config
        
        mock_web_server = Mock()
        mock_web_server.is_running = False  # Don't enter the loop
        mock_web_server_class.return_value = mock_web_server
        
        # Browser opening fails
        mock_browser.side_effect = Exception("Browser not found")
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main_ui()
        
        assert result is True
        output = mock_stdout.getvalue()
        assert "Could not open browser automatically" in output
        assert "Please manually open: http://127.0.0.1:8080" in output
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    @patch('src.youtube_notion.main.VideoProcessor')
    @patch('src.youtube_notion.main.QueueManager')
    @patch('src.youtube_notion.main.WebServerConfig')
    @patch('src.youtube_notion.main.WebServer')
    @patch('webbrowser.open')
    @patch('time.sleep')
    def test_main_ui_graceful_shutdown_timeout(self, mock_sleep, mock_browser, mock_web_server_class, 
                                             mock_web_config_class, mock_queue_manager_class, 
                                             mock_video_processor_class, mock_factory_class, 
                                             mock_load_config):
        """Test UI mode handles shutdown timeouts gracefully."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_metadata_extractor = Mock()
        mock_summary_writer = Mock()
        mock_storage = Mock()
        mock_factory.create_all_components.return_value = (mock_metadata_extractor, mock_summary_writer, mock_storage)
        
        mock_processor = Mock()
        mock_video_processor_class.return_value = mock_processor
        
        mock_queue_manager = Mock()
        mock_queue_manager.stop_processing.return_value = False  # Timeout
        mock_queue_manager_class.return_value = mock_queue_manager
        
        mock_web_config = Mock()
        mock_web_config.host = "127.0.0.1"
        mock_web_config.port = 8080
        mock_web_config_class.from_env.return_value = mock_web_config
        
        mock_web_server = Mock()
        mock_web_server.is_running = False  # Don't enter the loop
        mock_web_server.stop.return_value = False  # Timeout
        mock_web_server_class.return_value = mock_web_server
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main_ui()
        
        assert result is True
        output = mock_stdout.getvalue()
        assert "Web server shutdown timeout" in output
        assert "Queue processing shutdown timeout" in output
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    @patch('src.youtube_notion.main.VideoProcessor')
    @patch('src.youtube_notion.main.QueueManager')
    @patch('src.youtube_notion.main.WebServerConfig')
    @patch('src.youtube_notion.main.WebServer')
    @patch('webbrowser.open')
    @patch('time.sleep')
    def test_main_ui_output_formatting(self, mock_sleep, mock_browser, mock_web_server_class, 
                                     mock_web_config_class, mock_queue_manager_class, 
                                     mock_video_processor_class, mock_factory_class, 
                                     mock_load_config):
        """Test that UI mode produces properly formatted output."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_metadata_extractor = Mock()
        mock_summary_writer = Mock()
        mock_storage = Mock()
        mock_factory.create_all_components.return_value = (mock_metadata_extractor, mock_summary_writer, mock_storage)
        
        mock_processor = Mock()
        mock_video_processor_class.return_value = mock_processor
        
        mock_queue_manager = Mock()
        mock_queue_manager_class.return_value = mock_queue_manager
        
        mock_web_config = Mock()
        mock_web_config.host = "127.0.0.1"
        mock_web_config.port = 8080
        mock_web_config_class.from_env.return_value = mock_web_config
        
        mock_web_server = Mock()
        mock_web_server.is_running = False  # Don't enter the loop
        mock_web_server_class.return_value = mock_web_server
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main_ui()
        
        assert result is True
        output = mock_stdout.getvalue()
        
        # Check for expected output sections
        assert "YouTube to Notion Database Integration - Web UI Mode" in output
        assert "1. Loading configuration..." in output
        assert "2. Initializing components..." in output
        assert "3. Setting up web server..." in output
        assert "4. Starting services..." in output
        assert "5. Opening web browser" in output
        assert "WEB UI RUNNING" in output
        assert "Access the web interface at: http://127.0.0.1:8080" in output
        assert "Press Ctrl+C to stop the server" in output
        assert "WEB UI SHUTDOWN COMPLETE" in output


class TestMainUIIntegration:
    """Integration tests for main_ui function."""
    
    @patch('src.youtube_notion.main.load_application_config')
    def test_main_ui_requires_youtube_mode_config(self, mock_load_config):
        """Test that main_ui requires YouTube mode configuration."""
        mock_load_config.return_value = None
        
        result = main_ui()
        
        assert result is False
        mock_load_config.assert_called_once_with(youtube_mode=True)
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    @patch('src.youtube_notion.main.VideoProcessor')
    @patch('src.youtube_notion.main.QueueManager')
    @patch('src.youtube_notion.main.WebServerConfig')
    @patch('src.youtube_notion.main.WebServer')
    def test_main_ui_component_initialization_order(self, mock_web_server_class, mock_web_config_class,
                                                   mock_queue_manager_class, mock_video_processor_class,
                                                   mock_factory_class, mock_load_config):
        """Test that components are initialized in the correct order."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_metadata_extractor = Mock()
        mock_summary_writer = Mock()
        mock_storage = Mock()
        mock_factory.create_all_components.return_value = (mock_metadata_extractor, mock_summary_writer, mock_storage)
        
        mock_processor = Mock()
        mock_video_processor_class.return_value = mock_processor
        
        mock_queue_manager = Mock()
        mock_queue_manager_class.return_value = mock_queue_manager
        
        mock_web_config = Mock()
        mock_web_config.host = "127.0.0.1"
        mock_web_config.port = 8080
        mock_web_config_class.from_env.return_value = mock_web_config
        
        mock_web_server = Mock()
        mock_web_server.is_running = False  # Don't enter the loop
        mock_web_server_class.return_value = mock_web_server
        
        with patch('webbrowser.open'), patch('time.sleep'):
            result = main_ui()
        
        assert result is True
        
        # Verify initialization order
        assert mock_load_config.call_count == 1
        assert mock_factory_class.call_count == 1
        assert mock_factory.create_all_components.call_count == 1
        assert mock_video_processor_class.call_count == 1
        assert mock_processor.validate_configuration.call_count == 1
        assert mock_queue_manager_class.call_count == 1
        assert mock_web_config_class.from_env.call_count == 1
        assert mock_web_server_class.call_count == 1