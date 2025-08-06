"""
Tests for chat logging functionality.
"""

import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from src.youtube_notion.utils.chat_logger import ChatLogger
from src.youtube_notion.writers.gemini_summary_writer import GeminiSummaryWriter


class TestChatLogger:
    """Test the ChatLogger utility class."""
    
    def setup_method(self):
        """Set up test environment with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = ChatLogger(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_log_chat_creates_file(self):
        """Test that logging creates a file with correct content."""
        video_id = "test_video_123"
        video_url = f"https://youtu.be/{video_id}"
        prompt = "Test prompt"
        response = "Test response"
        metadata = {
            "title": "Test Video",
            "channel": "Test Channel",
            "published_at": "2024-01-01T00:00:00Z",
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        }
        
        # Log the chat
        log_file = self.logger.log_chat(video_id, video_url, prompt, response, metadata)
        
        # Verify file was created
        assert os.path.exists(log_file)
        assert log_file.startswith(os.path.join(self.temp_dir, video_id))
        assert log_file.endswith('.md')
        
        # Verify content
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# Gemini Chat Log" in content
        assert video_id in content
        assert video_url in content
        assert "Test Video" in content
        assert "Test Channel" in content
        assert prompt in content
        assert response in content
    
    def test_log_chat_without_metadata(self):
        """Test logging without video metadata."""
        video_id = "test_video_456"
        video_url = f"https://youtu.be/{video_id}"
        prompt = "Test prompt"
        response = "Test response"
        
        # Log without metadata
        log_file = self.logger.log_chat(video_id, video_url, prompt, response)
        
        # Verify file was created
        assert os.path.exists(log_file)
        
        # Verify content doesn't include metadata section
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# Gemini Chat Log" in content
        assert "## Video Metadata" not in content
    
    def test_get_log_files(self):
        """Test retrieving log files."""
        video_id = "test_video_789"
        other_video_id = "other_video_123"
        
        # Create test files manually to ensure different names
        test_files = [
            f"{video_id}_20240101_100000.md",
            f"{video_id}_20240101_100001.md", 
            f"{other_video_id}_20240101_100002.md"
        ]
        
        # Create the files
        for filename in test_files:
            filepath = Path(self.temp_dir) / filename
            filepath.write_text("# Test Log File\nTest content")
        
        # Get all log files
        all_files = self.logger.get_log_files()
        assert len(all_files) == 3
        
        # Get files for specific video
        video_files = self.logger.get_log_files(video_id)
        assert len(video_files) == 2
        
        # Get files for other video
        other_files = self.logger.get_log_files(other_video_id)
        assert len(other_files) == 1
        
        # Verify all returned files exist
        for file_path in video_files:
            assert file_path.exists()
            assert video_id in file_path.name


class TestGeminiSummaryWriterLogging:
    """Test chat logging integration in GeminiSummaryWriter."""
    
    def test_writer_logs_chat_on_success(self):
        """Test that writer logs chat when summary generation succeeds."""
        # Create a writer with mock chat logger
        writer = GeminiSummaryWriter(
            api_key="test_key",
            max_retries=1
        )
        
        # Mock the chat logger
        mock_logger = MagicMock()
        writer.chat_logger = mock_logger
        
        # Mock the API call to return a response
        with patch.object(writer, '_call_gemini_api', return_value="Test summary"):
            video_url = "https://youtu.be/dQw4w9WgXcQ"  # Valid 11-character video ID
            video_metadata = {
                "video_id": "dQw4w9WgXcQ",
                "title": "Test Video", 
                "channel": "Test Channel"
            }
            
            # Generate summary
            result = writer.generate_summary(video_url, video_metadata)
            
            # Verify the result
            assert result == "Test summary"
            
            # Verify chat was logged
            mock_logger.log_chat.assert_called_once_with(
                video_id="dQw4w9WgXcQ",
                video_url=video_url,
                prompt=writer.default_prompt,
                response="Test summary",
                video_metadata=video_metadata
            )
    
    def test_writer_handles_logging_failure_gracefully(self):
        """Test that writer continues working even if logging fails."""
        writer = GeminiSummaryWriter(
            api_key="test_key",
            max_retries=1
        )
        
        # Mock the chat logger to raise an exception
        mock_logger = MagicMock()
        mock_logger.log_chat.side_effect = Exception("Logging failed")
        writer.chat_logger = mock_logger
        
        # Mock the API call to return a response
        with patch.object(writer, '_call_gemini_api', return_value="Test summary"), \
             patch('builtins.print') as mock_print:  # Capture the warning print
            
            video_url = "https://youtu.be/dQw4w9WgXcQ"  # Valid 11-character video ID
            video_metadata = {
                "video_id": "dQw4w9WgXcQ",
                "title": "Test Video", 
                "channel": "Test Channel"
            }
            
            # Generate summary - should not raise exception
            result = writer.generate_summary(video_url, video_metadata)
            
            # Verify the result is still returned
            assert result == "Test summary"
            
            # Verify warning was printed
            mock_print.assert_called_once()
            assert "Warning: Failed to log chat conversation" in str(mock_print.call_args)