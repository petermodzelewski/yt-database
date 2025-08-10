"""
Tests for chat logging functionality.
"""

import os
import tempfile
import shutil
import time
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
    
    def test_log_chat_chunk_creates_file(self):
        """Test that logging a chunk creates a file with correct content."""
        video_id = "test_video_chunk_123"
        video_url = f"https://youtu.be/{video_id}"
        prompt = "Test chunk prompt"
        response = "Test chunk response"
        metadata = {
            "title": "Test Chunk Video",
            "channel": "Test Chunk Channel",
        }

        # Log the chat chunk
        log_file = self.logger.log_chat_chunk(
            video_id, video_url, prompt, response, metadata,
            chunk_index=1, start_offset=600, end_offset=1200
        )

        # Verify file was created
        assert os.path.exists(log_file)
        assert f"{video_id}_chunk_1" in os.path.basename(log_file)
        assert log_file.endswith('.md')

        # Verify content
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "# Gemini Chat Log (Chunk)" in content
        assert "Chunk Index**: 1" in content
        assert "Start Offset**: 600s" in content
        assert "End Offset**: 1200s" in content
        assert video_id in content
        assert video_url in content
        assert "Test Chunk Video" in content
        assert "Test Chunk Channel" in content
        assert prompt in content
        assert response in content

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
    
    def test_get_latest_log_path(self):
        """Test getting the latest log file path."""
        video_id = "test_video_latest"
        
        # Create test files with different timestamps
        import time
        test_files = []
        for i in range(3):
            filename = f"{video_id}_{i}_20240101_10000{i}.md"
            filepath = Path(self.temp_dir) / filename
            filepath.write_text(f"# Test Log File {i}\nTest content")
            test_files.append(filepath)
            time.sleep(0.01)  # Small delay to ensure different modification times
        
        # Get latest log path
        latest_path = self.logger.get_latest_log_path(video_id)
        
        assert latest_path is not None
        assert video_id in latest_path
        assert latest_path.endswith('.md')
        
        # Should be the last created file
        latest_file = Path(latest_path)
        assert latest_file.exists()
    
    def test_get_latest_log_path_no_files(self):
        """Test getting latest log path when no files exist."""
        latest_path = self.logger.get_latest_log_path("nonexistent_video")
        assert latest_path is None
    
    def test_get_latest_log_path_all_videos(self):
        """Test getting latest log path across all videos."""
        # Create files for different videos
        video_ids = ["video1", "video2", "video3"]
        for i, video_id in enumerate(video_ids):
            filename = f"{video_id}_20240101_10000{i}.md"
            filepath = Path(self.temp_dir) / filename
            filepath.write_text(f"# Test Log File {i}\nTest content")
            time.sleep(0.01)  # Ensure different modification times
        
        # Get latest across all videos (no video_id filter)
        latest_path = self.logger.get_latest_log_path()
        
        assert latest_path is not None
        assert "video3" in latest_path  # Should be the last created
    
    def test_get_chunk_log_paths(self):
        """Test getting chunk log file paths."""
        video_id = "chunked_video_123"
        
        # Create chunk log files in non-sequential order
        chunk_files = [
            f"{video_id}_chunk_2_20240101_100000.md",
            f"{video_id}_chunk_0_20240101_100001.md", 
            f"{video_id}_chunk_1_20240101_100002.md",
            f"{video_id}_chunk_10_20240101_100003.md"  # Test double-digit sorting
        ]
        
        # Create the files
        for filename in chunk_files:
            filepath = Path(self.temp_dir) / filename
            filepath.write_text(f"# Chunk Log File\nChunk content for {filename}")
        
        # Get chunk log paths
        chunk_paths = self.logger.get_chunk_log_paths(video_id)
        
        assert len(chunk_paths) == 4
        
        # Verify they are sorted by chunk index
        chunk_indices = []
        for path in chunk_paths:
            filename = Path(path).stem
            # Extract chunk index from filename
            parts = filename.split('_')
            chunk_idx = None
            for i, part in enumerate(parts):
                if part == 'chunk' and i + 1 < len(parts):
                    chunk_idx = int(parts[i + 1])
                    break
            chunk_indices.append(chunk_idx)
        
        assert chunk_indices == [0, 1, 2, 10]  # Should be sorted numerically
        
        # Verify all files exist
        for path in chunk_paths:
            assert os.path.exists(path)
            assert video_id in path
            assert "chunk" in path
    
    def test_get_chunk_log_paths_no_chunks(self):
        """Test getting chunk log paths when no chunk files exist."""
        chunk_paths = self.logger.get_chunk_log_paths("no_chunks_video")
        assert chunk_paths == []
    
    def test_get_chunk_log_paths_mixed_files(self):
        """Test getting chunk log paths with mixed file types."""
        video_id = "mixed_video_456"
        
        # Create mix of regular and chunk log files
        files = [
            f"{video_id}_20240101_100000.md",  # Regular log
            f"{video_id}_chunk_0_20240101_100001.md",  # Chunk log
            f"{video_id}_chunk_1_20240101_100002.md",  # Chunk log
            f"{video_id}_summary_20240101_100003.md",  # Other type
        ]
        
        for filename in files:
            filepath = Path(self.temp_dir) / filename
            filepath.write_text(f"# Log File\nContent for {filename}")
        
        # Get only chunk log paths
        chunk_paths = self.logger.get_chunk_log_paths(video_id)
        
        assert len(chunk_paths) == 2
        for path in chunk_paths:
            assert "chunk" in path
            assert video_id in path
    
    def test_get_chunk_log_paths_invalid_chunk_indices(self):
        """Test handling of invalid chunk indices in filenames."""
        video_id = "invalid_chunks_789"
        
        # Create files with invalid chunk indices
        files = [
            f"{video_id}_chunk_abc_20240101_100000.md",  # Non-numeric
            f"{video_id}_chunk_0_20240101_100001.md",    # Valid
            f"{video_id}_chunk__20240101_100002.md",     # Missing index
            f"{video_id}_chunk_1_20240101_100003.md",    # Valid
        ]
        
        for filename in files:
            filepath = Path(self.temp_dir) / filename
            filepath.write_text(f"# Log File\nContent for {filename}")
        
        # Get chunk log paths - should handle invalid indices gracefully
        chunk_paths = self.logger.get_chunk_log_paths(video_id)
        
        # Should return all files but with invalid ones sorted to beginning (index 0)
        assert len(chunk_paths) == 4
        
        # Valid chunks should still be in correct order
        valid_chunks = [path for path in chunk_paths if "_chunk_0_" in path or "_chunk_1_" in path]
        assert len(valid_chunks) == 2


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