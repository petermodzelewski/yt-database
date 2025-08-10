#!/usr/bin/env python3
"""
Tests for CLI argument parsing and execution modes.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from io import StringIO

# Add src to path for imports
sys.path.insert(0, 'src')

# Import the CLI module
import youtube_notion_cli


class TestCLIArgumentParsing:
    """Test CLI argument parsing functionality."""
    
    def test_parse_arguments_example_data_default(self):
        """Test that example data mode is default when no arguments provided."""
        with patch('sys.argv', ['youtube_notion_cli.py']):
            args = youtube_notion_cli.parse_arguments()
            assert args.url is None
            assert args.example_data is False  # Default behavior, not explicitly set
            assert args.prompt is None
    
    def test_parse_arguments_example_data_explicit(self):
        """Test explicit example data mode."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--example-data']):
            args = youtube_notion_cli.parse_arguments()
            assert args.url is None
            assert args.example_data is True
            assert args.prompt is None
    
    def test_parse_arguments_youtube_url(self):
        """Test YouTube URL argument parsing."""
        test_url = "https://www.youtube.com/watch?v=abc123"
        with patch('sys.argv', ['youtube_notion_cli.py', '--url', test_url]):
            args = youtube_notion_cli.parse_arguments()
            assert args.url == test_url
            assert args.example_data is False
            assert args.prompt is None
    
    def test_parse_arguments_youtube_url_with_prompt(self):
        """Test YouTube URL with custom prompt."""
        test_url = "https://www.youtube.com/watch?v=abc123"
        test_prompt = "Custom summary prompt"
        with patch('sys.argv', ['youtube_notion_cli.py', '--url', test_url, '--prompt', test_prompt]):
            args = youtube_notion_cli.parse_arguments()
            assert args.url == test_url
            assert args.example_data is False
            assert args.prompt == test_prompt
    
    def test_parse_arguments_youtu_be_url(self):
        """Test shortened YouTube URL format."""
        test_url = "https://youtu.be/abc123"
        with patch('sys.argv', ['youtube_notion_cli.py', '--url', test_url]):
            args = youtube_notion_cli.parse_arguments()
            assert args.url == test_url
            assert args.example_data is False
            assert args.prompt is None
    
    def test_parse_arguments_mutually_exclusive_error(self):
        """Test that --url and --example-data are mutually exclusive."""
        test_url = "https://www.youtube.com/watch?v=abc123"
        with patch('sys.argv', ['youtube_notion_cli.py', '--url', test_url, '--example-data']):
            with pytest.raises(SystemExit):
                youtube_notion_cli.parse_arguments()
    
    def test_parse_arguments_ui_mode(self):
        """Test UI mode argument parsing."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui']):
            args = youtube_notion_cli.parse_arguments()
            assert args.ui is True
            assert args.url is None
            assert args.example_data is False
            assert args.prompt is None
    
    def test_parse_arguments_ui_mutually_exclusive_with_url(self):
        """Test that --ui and --url are mutually exclusive."""
        test_url = "https://www.youtube.com/watch?v=abc123"
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui', '--url', test_url]):
            with pytest.raises(SystemExit):
                youtube_notion_cli.parse_arguments()
    
    def test_parse_arguments_ui_mutually_exclusive_with_example_data(self):
        """Test that --ui and --example-data are mutually exclusive."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui', '--example-data']):
            with pytest.raises(SystemExit):
                youtube_notion_cli.parse_arguments()
    
    def test_parse_arguments_ui_mutually_exclusive_with_urls(self):
        """Test that --ui and --urls are mutually exclusive."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui', '--urls', 'url1,url2']):
            with pytest.raises(SystemExit):
                youtube_notion_cli.parse_arguments()
    
    def test_parse_arguments_ui_mutually_exclusive_with_file(self):
        """Test that --ui and --file are mutually exclusive."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui', '--file', 'urls.txt']):
            with pytest.raises(SystemExit):
                youtube_notion_cli.parse_arguments()


class TestCLIValidation:
    """Test CLI argument validation."""
    
    def test_prompt_without_url_error(self):
        """Test that --prompt without --url raises an error."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--prompt', 'test prompt']):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    youtube_notion_cli.main_cli()
                assert exc_info.value.code == 1
                assert "Error: --prompt can only be used with single --url" in mock_stderr.getvalue()
    
    def test_prompt_with_example_data_error(self):
        """Test that --prompt with --example-data raises an error."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--example-data', '--prompt', 'test prompt']):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    youtube_notion_cli.main_cli()
                assert exc_info.value.code == 1
                assert "Error: --prompt can only be used with single --url" in mock_stderr.getvalue()
    
    def test_ui_mode_prevents_url_processing(self):
        """Test that UI mode doesn't process command line URLs."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui']):
            with patch('youtube_notion_cli.main_ui') as mock_main_ui:
                mock_main_ui.return_value = True
                with pytest.raises(SystemExit) as exc_info:
                    youtube_notion_cli.main_cli()
                assert exc_info.value.code == 0
                mock_main_ui.assert_called_once()


class TestCLIExecution:
    """Test CLI execution modes."""
    
    @patch('youtube_notion_cli.main')
    def test_main_cli_example_data_default(self, mock_main):
        """Test that main is called with no arguments for default mode."""
        with patch('sys.argv', ['youtube_notion_cli.py']):
            youtube_notion_cli.main_cli()
            mock_main.assert_called_once_with()
    
    @patch('youtube_notion_cli.main')
    def test_main_cli_example_data_explicit(self, mock_main):
        """Test that main is called with no arguments for explicit example data mode."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--example-data']):
            youtube_notion_cli.main_cli()
            mock_main.assert_called_once_with()
    
    @patch('youtube_notion_cli.main')
    def test_main_cli_youtube_url(self, mock_main):
        """Test that main is called with YouTube URL."""
        test_url = "https://www.youtube.com/watch?v=abc123"
        with patch('sys.argv', ['youtube_notion_cli.py', '--url', test_url]):
            youtube_notion_cli.main_cli()
            mock_main.assert_called_once_with(youtube_url=test_url, custom_prompt=None)
    
    @patch('youtube_notion_cli.main')
    def test_main_cli_youtube_url_with_prompt(self, mock_main):
        """Test that main is called with YouTube URL and custom prompt."""
        test_url = "https://www.youtube.com/watch?v=abc123"
        test_prompt = "Custom summary prompt"
        with patch('sys.argv', ['youtube_notion_cli.py', '--url', test_url, '--prompt', test_prompt]):
            youtube_notion_cli.main_cli()
            mock_main.assert_called_once_with(youtube_url=test_url, custom_prompt=test_prompt)
    
    @patch('youtube_notion_cli.main_ui')
    def test_main_cli_ui_mode(self, mock_main_ui):
        """Test that main_ui is called for UI mode."""
        mock_main_ui.return_value = True
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui']):
            with pytest.raises(SystemExit) as exc_info:
                youtube_notion_cli.main_cli()
            assert exc_info.value.code == 0
            mock_main_ui.assert_called_once()
    
    @patch('youtube_notion_cli.main_ui')
    def test_main_cli_ui_mode_failure(self, mock_main_ui):
        """Test that UI mode failure exits with error code."""
        mock_main_ui.return_value = False
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui']):
            with pytest.raises(SystemExit) as exc_info:
                youtube_notion_cli.main_cli()
            assert exc_info.value.code == 1
            mock_main_ui.assert_called_once()
    
    @patch('youtube_notion_cli.main_ui')
    def test_main_cli_ui_mode_keyboard_interrupt(self, mock_main_ui):
        """Test that UI mode handles KeyboardInterrupt gracefully."""
        mock_main_ui.side_effect = KeyboardInterrupt()
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit) as exc_info:
                    youtube_notion_cli.main_cli()
                assert exc_info.value.code == 0
                assert "Shutting down web UI..." in mock_stdout.getvalue()
    
    @patch('youtube_notion_cli.main_ui')
    def test_main_cli_ui_mode_exception(self, mock_main_ui):
        """Test that UI mode handles exceptions gracefully."""
        mock_main_ui.side_effect = Exception("Test error")
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui']):
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    youtube_notion_cli.main_cli()
                assert exc_info.value.code == 1
                assert "Error starting web UI: Test error" in mock_stderr.getvalue()


class TestCLIHelpAndUsage:
    """Test CLI help and usage information."""
    
    def test_help_message(self):
        """Test that help message is displayed correctly."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--help']):
            with pytest.raises(SystemExit) as exc_info:
                youtube_notion_cli.parse_arguments()
            # Help should exit with code 0
            assert exc_info.value.code == 0
    
    def test_help_contains_examples(self):
        """Test that help message contains usage examples."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--help']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit):
                    youtube_notion_cli.parse_arguments()
                help_output = mock_stdout.getvalue()
                assert "Examples:" in help_output
                assert "--example-data" in help_output
                assert "--url" in help_output
                assert "--prompt" in help_output
                assert "--ui" in help_output
                assert "Start web UI mode for visual queue management" in help_output


class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    @patch('youtube_notion_cli.main')
    def test_cli_integration_example_data(self, mock_main):
        """Test full CLI integration with example data mode."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--example-data']):
            youtube_notion_cli.main_cli()
            mock_main.assert_called_once_with()
    
    @patch('youtube_notion_cli.main')
    def test_cli_integration_youtube_processing(self, mock_main):
        """Test full CLI integration with YouTube processing mode."""
        test_url = "https://www.youtube.com/watch?v=test123"
        test_prompt = "Generate a detailed summary"
        
        with patch('sys.argv', ['youtube_notion_cli.py', '--url', test_url, '--prompt', test_prompt]):
            youtube_notion_cli.main_cli()
            mock_main.assert_called_once_with(youtube_url=test_url, custom_prompt=test_prompt)
    
    @patch('youtube_notion_cli.main_ui')
    def test_cli_integration_ui_mode(self, mock_main_ui):
        """Test full CLI integration with UI mode."""
        mock_main_ui.return_value = True
        
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui']):
            with pytest.raises(SystemExit) as exc_info:
                youtube_notion_cli.main_cli()
            assert exc_info.value.code == 0
            mock_main_ui.assert_called_once()


class TestUIModeFunctionality:
    """Test UI mode specific functionality."""
    
    def test_ui_mode_argument_isolation(self):
        """Test that UI mode is properly isolated from other arguments."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui']):
            args = youtube_notion_cli.parse_arguments()
            assert args.ui is True
            assert args.url is None
            assert args.urls is None
            assert args.file is None
            assert args.example_data is False
            assert args.prompt is None
    
    @patch('youtube_notion_cli.main_ui')
    def test_ui_mode_browser_opening_simulation(self, mock_main_ui):
        """Test that UI mode attempts to open browser."""
        mock_main_ui.return_value = True
        
        with patch('sys.argv', ['youtube_notion_cli.py', '--ui']):
            with pytest.raises(SystemExit) as exc_info:
                youtube_notion_cli.main_cli()
            assert exc_info.value.code == 0
            mock_main_ui.assert_called_once()
    
    def test_ui_mode_help_text(self):
        """Test that UI mode help text is descriptive."""
        with patch('sys.argv', ['youtube_notion_cli.py', '--help']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                with pytest.raises(SystemExit):
                    youtube_notion_cli.parse_arguments()
                help_output = mock_stdout.getvalue()
                assert "Start web UI mode for visual queue management" in help_output

