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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])