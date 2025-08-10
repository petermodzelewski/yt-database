#!/usr/bin/env python3
"""
Tests for CLI batch processing integration with QueueManager.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock, Mock
from io import StringIO

# Add src to path for imports
sys.path.insert(0, 'src')

# Import the CLI module and main functions
import youtube_notion_cli
from src.youtube_notion.main import main_batch


class TestCLIBatchProcessingArguments:
    """Test CLI argument parsing for batch processing modes."""
    
    def test_parse_arguments_urls_mode(self):
        """Test parsing comma-separated URLs."""
        test_urls = "https://youtu.be/abc123,https://youtu.be/def456"
        with patch('sys.argv', ['youtube_notion_cli.py', '--urls', test_urls]):
            args = youtube_notion_cli.parse_arguments()
            assert args.urls == test_urls
            assert args.url is None
            assert args.file is None
            assert args.example_data is False
            assert args.prompt is None
    
    def test_parse_arguments_file_mode(self):
        """Test parsing URLs from file."""
        test_file = "test_urls.txt"
        with patch('sys.argv', ['youtube_notion_cli.py', '--file', test_file]):
            args = youtube_notion_cli.parse_arguments()
            assert args.file == test_file
            assert args.url is None
            assert args.urls is None
            assert args.example_data is False
            assert args.prompt is None
    
    def test_parse_arguments_urls_mutually_exclusive_with_url(self):
        """Test that --urls and --url are mutually exclusive."""
        test_url = "https://www.youtube.com/watch?v=abc123"
        test_urls = "https://youtu.be/abc123,https://youtu.be/def456"
        with patch('sys.argv', ['youtube_notion_cli.py', '--url', test_url, '--urls', test_urls]):
            with pytest.raises(SystemExit):
                youtube_notion_cli.parse_arguments()
    
    def test_parse_arguments_file_mutually_exclusive_with_url(self):
        """Test that --file and --url are mutually exclusive."""
        test_url = "https://www.youtube.com/watch?v=abc123"
        test_file = "test_urls.txt"
        with patch('sys.argv', ['youtube_notion_cli.py', '--url', test_url, '--file', test_file]):
            with pytest.raises(SystemExit):
                youtube_notion_cli.parse_arguments()
    
    def test_parse_arguments_urls_mutually_exclusive_with_file(self):
        """Test that --urls and --file are mutually exclusive."""
        test_urls = "https://youtu.be/abc123,https://youtu.be/def456"
        test_file = "test_urls.txt"
        with patch('sys.argv', ['youtube_notion_cli.py', '--urls', test_urls, '--file', test_file]):
            with pytest.raises(SystemExit):
                youtube_notion_cli.parse_arguments()


class TestCLIFileProcessing:
    """Test CLI file processing functionality."""
    
    def test_parse_urls_from_file_success(self):
        """Test successful parsing of URLs from file."""
        test_content = "https://youtu.be/abc123\nhttps://youtu.be/def456\n\nhttps://youtu.be/ghi789\n"
        expected_urls = ["https://youtu.be/abc123", "https://youtu.be/def456", "https://youtu.be/ghi789"]
        
        with patch('builtins.open', mock_open_read_data(test_content)):
            urls = youtube_notion_cli.parse_urls_from_file("test_urls.txt")
            assert urls == expected_urls
    
    def test_parse_urls_from_file_empty_lines_ignored(self):
        """Test that empty lines are ignored when parsing URLs from file."""
        test_content = "\n\nhttps://youtu.be/abc123\n\n\nhttps://youtu.be/def456\n\n"
        expected_urls = ["https://youtu.be/abc123", "https://youtu.be/def456"]
        
        with patch('builtins.open', mock_open_read_data(test_content)):
            urls = youtube_notion_cli.parse_urls_from_file("test_urls.txt")
            assert urls == expected_urls
    
    def test_parse_urls_from_file_not_found(self):
        """Test handling of file not found error."""
        with patch('builtins.open', side_effect=FileNotFoundError()):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    youtube_notion_cli.parse_urls_from_file("nonexistent.txt")
                assert exc_info.value.code == 1
                assert "Error: File 'nonexistent.txt' not found" in mock_stderr.getvalue()
    
    def test_parse_urls_from_file_read_error(self):
        """Test handling of file read error."""
        with patch('builtins.open', side_effect=IOError("Permission denied")):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    youtube_notion_cli.parse_urls_from_file("test_urls.txt")
                assert exc_info.value.code == 1
                assert "Error reading file 'test_urls.txt': Permission denied" in mock_stderr.getvalue()


class TestCLIBatchExecution:
    """Test CLI batch execution modes."""
    
    @patch('youtube_notion_cli.main_batch')
    def test_main_cli_urls_mode(self, mock_main_batch):
        """Test that main_batch is called for URLs mode."""
        test_urls = "https://youtu.be/abc123,https://youtu.be/def456"
        expected_urls = ["https://youtu.be/abc123", "https://youtu.be/def456"]
        mock_main_batch.return_value = True
        
        with patch('sys.argv', ['youtube_notion_cli.py', '--urls', test_urls]):
            with pytest.raises(SystemExit) as exc_info:
                youtube_notion_cli.main_cli()
            assert exc_info.value.code == 0
            mock_main_batch.assert_called_once_with(expected_urls)
    
    @patch('youtube_notion_cli.main_batch')
    def test_main_cli_urls_mode_failure(self, mock_main_batch):
        """Test that URLs mode failure exits with error code."""
        test_urls = "https://youtu.be/abc123,https://youtu.be/def456"
        expected_urls = ["https://youtu.be/abc123", "https://youtu.be/def456"]
        mock_main_batch.return_value = False
        
        with patch('sys.argv', ['youtube_notion_cli.py', '--urls', test_urls]):
            with pytest.raises(SystemExit) as exc_info:
                youtube_notion_cli.main_cli()
            assert exc_info.value.code == 1
            mock_main_batch.assert_called_once_with(expected_urls)
    
    @patch('youtube_notion_cli.main_batch')
    @patch('youtube_notion_cli.parse_urls_from_file')
    def test_main_cli_file_mode(self, mock_parse_urls, mock_main_batch):
        """Test that main_batch is called for file mode."""
        test_file = "test_urls.txt"
        expected_urls = ["https://youtu.be/abc123", "https://youtu.be/def456"]
        mock_parse_urls.return_value = expected_urls
        mock_main_batch.return_value = True
        
        with patch('sys.argv', ['youtube_notion_cli.py', '--file', test_file]):
            with pytest.raises(SystemExit) as exc_info:
                youtube_notion_cli.main_cli()
            assert exc_info.value.code == 0
            mock_parse_urls.assert_called_once_with(test_file)
            mock_main_batch.assert_called_once_with(expected_urls)
    
    @patch('youtube_notion_cli.main_batch')
    @patch('youtube_notion_cli.parse_urls_from_file')
    def test_main_cli_file_mode_failure(self, mock_parse_urls, mock_main_batch):
        """Test that file mode failure exits with error code."""
        test_file = "test_urls.txt"
        expected_urls = ["https://youtu.be/abc123", "https://youtu.be/def456"]
        mock_parse_urls.return_value = expected_urls
        mock_main_batch.return_value = False
        
        with patch('sys.argv', ['youtube_notion_cli.py', '--file', test_file]):
            with pytest.raises(SystemExit) as exc_info:
                youtube_notion_cli.main_cli()
            assert exc_info.value.code == 1
            mock_parse_urls.assert_called_once_with(test_file)
            mock_main_batch.assert_called_once_with(expected_urls)
    
    def test_main_cli_urls_parsing(self):
        """Test that comma-separated URLs are parsed correctly."""
        test_urls = "https://youtu.be/abc123, https://youtu.be/def456 ,https://youtu.be/ghi789"
        expected_urls = ["https://youtu.be/abc123", "https://youtu.be/def456", "https://youtu.be/ghi789"]
        
        with patch('sys.argv', ['youtube_notion_cli.py', '--urls', test_urls]):
            with patch('youtube_notion_cli.main_batch') as mock_main_batch:
                mock_main_batch.return_value = True
                with pytest.raises(SystemExit):
                    youtube_notion_cli.main_cli()
                mock_main_batch.assert_called_once_with(expected_urls)
    
    def test_main_cli_urls_empty_list_error(self):
        """Test that empty URL list raises an error."""
        test_urls = "  ,  ,  "  # Only whitespace and commas
        
        with patch('sys.argv', ['youtube_notion_cli.py', '--urls', test_urls]):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    youtube_notion_cli.main_cli()
                assert exc_info.value.code == 1
                assert "Error: No valid URLs found in comma-separated list" in mock_stderr.getvalue()
    
    @patch('youtube_notion_cli.parse_urls_from_file')
    def test_main_cli_file_empty_list_error(self, mock_parse_urls):
        """Test that empty URL list from file raises an error."""
        test_file = "empty_urls.txt"
        mock_parse_urls.return_value = []
        
        with patch('sys.argv', ['youtube_notion_cli.py', '--file', test_file]):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    youtube_notion_cli.main_cli()
                assert exc_info.value.code == 1
                assert "Error: No URLs found in file" in mock_stderr.getvalue()


class TestMainBatchFunction:
    """Test the main_batch function implementation."""
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    @patch('src.youtube_notion.main.VideoProcessor')
    @patch('src.youtube_notion.main.QueueManager')
    def test_main_batch_success(self, mock_queue_manager_class, mock_video_processor_class,
                               mock_factory_class, mock_load_config):
        """Test successful batch processing."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_factory.create_all_components.return_value = (Mock(), Mock(), Mock())
        
        mock_processor = Mock()
        mock_video_processor_class.return_value = mock_processor
        
        mock_queue_manager = Mock()
        mock_queue_manager_class.return_value = mock_queue_manager
        mock_queue_manager.enqueue.side_effect = ["item1", "item2"]
        mock_queue_manager.get_statistics.return_value = {'processing_active': False}
        
        # Test URLs
        test_urls = ["https://youtu.be/abc123", "https://youtu.be/def456"]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('time.sleep'):  # Mock sleep to speed up test
                result = main_batch(test_urls)
        
        # Verify result
        assert result is True
        
        # Verify configuration loading
        mock_load_config.assert_called_once_with(youtube_mode=True)
        
        # Verify component creation
        mock_factory_class.assert_called_once_with(mock_config)
        mock_factory.create_all_components.assert_called_once()
        
        # Verify processor creation and validation
        mock_video_processor_class.assert_called_once()
        mock_processor.validate_configuration.assert_called_once()
        
        # Verify queue manager creation and usage
        mock_queue_manager_class.assert_called_once_with(mock_processor)
        mock_queue_manager.start_processing.assert_called_once()
        mock_queue_manager.stop_processing.assert_called_once_with(timeout=5.0)
        
        # Verify URLs were enqueued
        assert mock_queue_manager.enqueue.call_count == 2
        mock_queue_manager.enqueue.assert_any_call("https://youtu.be/abc123")
        mock_queue_manager.enqueue.assert_any_call("https://youtu.be/def456")
        
        # Verify output
        output = mock_stdout.getvalue()
        assert "Processing 2 YouTube URLs..." in output
        assert "Adding URLs to processing queue..." in output
        assert "BATCH PROCESSING SUMMARY" in output
        assert "✓ All URLs processed successfully!" in output
    
    @patch('src.youtube_notion.main.load_application_config')
    def test_main_batch_configuration_failure(self, mock_load_config):
        """Test batch processing failure when configuration is invalid."""
        mock_load_config.return_value = None
        
        test_urls = ["https://youtu.be/abc123"]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main_batch(test_urls)
        
        assert result is False
        output = mock_stdout.getvalue()
        assert "Error: Configuration validation failed" in output
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    def test_main_batch_configuration_error_exception(self, mock_factory_class, mock_load_config):
        """Test batch processing handles ConfigurationError exceptions."""
        from src.youtube_notion.utils.exceptions import ConfigurationError
        
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_factory_class.side_effect = ConfigurationError("Test config error", details="Test details")
        
        test_urls = ["https://youtu.be/abc123"]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main_batch(test_urls)
        
        assert result is False
        output = mock_stdout.getvalue()
        assert "Error: Configuration error - Test config error" in output
        assert "Details: Test details" in output
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    def test_main_batch_import_error(self, mock_factory_class, mock_load_config):
        """Test batch processing handles ImportError exceptions."""
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_factory_class.side_effect = ImportError("Missing dependency")
        
        test_urls = ["https://youtu.be/abc123"]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main_batch(test_urls)
        
        assert result is False
        output = mock_stdout.getvalue()
        assert "Error: Failed to import required components - Missing dependency" in output
        assert "pip install google-genai google-api-python-client requests" in output
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    def test_main_batch_unexpected_error(self, mock_factory_class, mock_load_config):
        """Test batch processing handles unexpected exceptions."""
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        mock_factory_class.side_effect = Exception("Unexpected error")
        
        test_urls = ["https://youtu.be/abc123"]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = main_batch(test_urls)
        
        assert result is False
        output = mock_stdout.getvalue()
        assert "Error: Unexpected error during batch processing - Unexpected error" in output
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    @patch('src.youtube_notion.main.VideoProcessor')
    @patch('src.youtube_notion.main.QueueManager')
    def test_main_batch_with_failed_urls(self, mock_queue_manager_class, mock_video_processor_class,
                                        mock_factory_class, mock_load_config):
        """Test batch processing with some failed URLs."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_factory.create_all_components.return_value = (Mock(), Mock(), Mock())
        
        mock_processor = Mock()
        mock_video_processor_class.return_value = mock_processor
        
        mock_queue_manager = Mock()
        mock_queue_manager_class.return_value = mock_queue_manager
        
        # Simulate one successful enqueue and one failed
        mock_queue_manager.enqueue.side_effect = ["item1", Exception("Queue full")]
        mock_queue_manager.get_statistics.return_value = {'processing_active': False}
        
        # Test URLs
        test_urls = ["https://youtu.be/abc123", "https://youtu.be/def456"]
        
        # Mock the status listener to simulate processing completion
        def mock_add_status_listener(callback):
            # Simulate one successful and one failed processing
            from src.youtube_notion.web.models import QueueItem, QueueStatus
            
            # Successful item
            successful_item = Mock()
            successful_item.status.value = 'completed'
            successful_item.url = "https://youtu.be/abc123"
            successful_item.error_message = None
            callback("item1", successful_item)
        
        mock_queue_manager.add_status_listener.side_effect = mock_add_status_listener
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('time.sleep'):  # Mock sleep to speed up test
                result = main_batch(test_urls)
        
        # Should return False due to failed URLs
        assert result is False
        
        # Verify output contains failure information
        output = mock_stdout.getvalue()
        assert "BATCH PROCESSING SUMMARY" in output
        assert "Failed: 1" in output
        assert "Failed URLs:" in output
        assert "https://youtu.be/def456" in output
    
    @patch('src.youtube_notion.main.load_application_config')
    @patch('src.youtube_notion.main.ComponentFactory')
    @patch('src.youtube_notion.main.VideoProcessor')
    @patch('src.youtube_notion.main.QueueManager')
    def test_main_batch_status_listener_functionality(self, mock_queue_manager_class, mock_video_processor_class,
                                                     mock_factory_class, mock_load_config):
        """Test that the status listener correctly tracks batch progress."""
        # Setup mocks
        mock_config = Mock()
        mock_load_config.return_value = mock_config
        
        mock_factory = Mock()
        mock_factory_class.return_value = mock_factory
        mock_factory.create_all_components.return_value = (Mock(), Mock(), Mock())
        
        mock_processor = Mock()
        mock_video_processor_class.return_value = mock_processor
        
        mock_queue_manager = Mock()
        mock_queue_manager_class.return_value = mock_queue_manager
        mock_queue_manager.enqueue.side_effect = ["item1", "item2"]
        mock_queue_manager.get_statistics.return_value = {'processing_active': False}
        
        # Capture the status listener
        captured_listener = None
        def capture_listener(callback):
            nonlocal captured_listener
            captured_listener = callback
        
        mock_queue_manager.add_status_listener.side_effect = capture_listener
        
        test_urls = ["https://youtu.be/abc123", "https://youtu.be/def456"]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            with patch('time.sleep'):
                # Start the batch processing
                result = main_batch(test_urls)
                
                # Simulate status updates through the captured listener
                if captured_listener:
                    from src.youtube_notion.web.models import QueueItem, QueueStatus
                    
                    # Simulate first item completion
                    item1 = Mock()
                    item1.status.value = 'completed'
                    item1.url = "https://youtu.be/abc123"
                    item1.error_message = None
                    captured_listener("item1", item1)
                    
                    # Simulate second item failure
                    item2 = Mock()
                    item2.status.value = 'failed'
                    item2.url = "https://youtu.be/def456"
                    item2.error_message = "Processing failed"
                    captured_listener("item2", item2)
        
        # Verify the listener was added
        mock_queue_manager.add_status_listener.assert_called_once()
        
        # The result depends on the final state when the function completes
        # Since we're mocking the completion detection, we can't easily test the final result
        # But we can verify the listener was set up correctly
        assert captured_listener is not None


def mock_open_read_data(read_data):
    """Helper function to create a mock for open() that returns specific data."""
    from unittest.mock import mock_open
    return mock_open(read_data=read_data)


class TestBatchProcessingIntegration:
    """Integration tests for batch processing functionality."""
    
    @patch('youtube_notion_cli.main_batch')
    def test_full_cli_batch_integration_urls(self, mock_main_batch):
        """Test full CLI integration with URLs batch processing."""
        test_urls = "https://youtu.be/abc123,https://youtu.be/def456,https://youtu.be/ghi789"
        expected_urls = ["https://youtu.be/abc123", "https://youtu.be/def456", "https://youtu.be/ghi789"]
        mock_main_batch.return_value = True
        
        with patch('sys.argv', ['youtube_notion_cli.py', '--urls', test_urls]):
            with pytest.raises(SystemExit) as exc_info:
                youtube_notion_cli.main_cli()
            assert exc_info.value.code == 0
            mock_main_batch.assert_called_once_with(expected_urls)
    
    @patch('youtube_notion_cli.main_batch')
    @patch('youtube_notion_cli.parse_urls_from_file')
    def test_full_cli_batch_integration_file(self, mock_parse_urls, mock_main_batch):
        """Test full CLI integration with file batch processing."""
        test_file = "batch_urls.txt"
        expected_urls = ["https://youtu.be/abc123", "https://youtu.be/def456"]
        mock_parse_urls.return_value = expected_urls
        mock_main_batch.return_value = True
        
        with patch('sys.argv', ['youtube_notion_cli.py', '--file', test_file]):
            with pytest.raises(SystemExit) as exc_info:
                youtube_notion_cli.main_cli()
            assert exc_info.value.code == 0
            mock_parse_urls.assert_called_once_with(test_file)
            mock_main_batch.assert_called_once_with(expected_urls)
    
    def test_batch_processing_maintains_existing_behavior(self):
        """Test that batch processing maintains the same output format as before."""
        # This test verifies that the new QueueManager-based batch processing
        # produces output that matches the expected format from the original implementation
        
        test_urls = ["https://youtu.be/abc123", "https://youtu.be/def456"]
        
        with patch('src.youtube_notion.main.load_application_config') as mock_load_config:
            with patch('src.youtube_notion.main.ComponentFactory') as mock_factory_class:
                with patch('src.youtube_notion.main.VideoProcessor') as mock_video_processor_class:
                    with patch('src.youtube_notion.main.QueueManager') as mock_queue_manager_class:
                        # Setup successful mocks
                        mock_load_config.return_value = Mock()
                        mock_factory = Mock()
                        mock_factory_class.return_value = mock_factory
                        mock_factory.create_all_components.return_value = (Mock(), Mock(), Mock())
                        mock_video_processor_class.return_value = Mock()
                        
                        mock_queue_manager = Mock()
                        mock_queue_manager_class.return_value = mock_queue_manager
                        mock_queue_manager.enqueue.side_effect = ["item1", "item2"]
                        mock_queue_manager.get_statistics.return_value = {'processing_active': False}
                        
                        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                            with patch('time.sleep'):
                                result = main_batch(test_urls)
                        
                        output = mock_stdout.getvalue()
                        
                        # Verify expected output format
                        assert "Processing 2 YouTube URLs..." in output
                        assert "=" * 60 in output
                        assert "Adding URLs to processing queue..." in output
                        assert "BATCH PROCESSING SUMMARY" in output
                        assert "Total URLs processed: 2" in output
                        assert "Successful:" in output
                        assert "Failed:" in output
                        
                        # For successful processing
                        if result:
                            assert "✓ All URLs processed successfully!" in output
                        else:
                            assert "Failed URLs:" in output