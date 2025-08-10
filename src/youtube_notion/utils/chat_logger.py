"""
Chat logging utility for saving Gemini API conversations.

This module provides functionality to save chat logs from Gemini API
interactions for review and debugging purposes.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class ChatLogger:
    """
    Utility class for logging Gemini API chat conversations.
    
    Saves chat logs as markdown files with structured format including
    timestamps, video information, and full conversation history.
    """
    
    def __init__(self, log_directory: str = "chat_logs"):
        """
        Initialize the chat logger.
        
        Args:
            log_directory: Directory to save chat logs (default: "chat_logs")
        """
        self.log_directory = Path(log_directory)
        self._ensure_log_directory()
    
    def _ensure_log_directory(self):
        """Create the log directory if it doesn't exist."""
        self.log_directory.mkdir(exist_ok=True)
    
    def log_chat(self, video_id: str, video_url: str, prompt: str, 
                 response: str, video_metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Log a chat conversation to a markdown file.
        
        Args:
            video_id: YouTube video ID
            video_url: Full YouTube URL
            prompt: The prompt sent to Gemini
            response: The response received from Gemini
            video_metadata: Optional video metadata (title, channel, etc.)
            
        Returns:
            str: Path to the created log file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{video_id}_{timestamp}.md"
        filepath = self.log_directory / filename
        
        # Prepare log content
        log_content = self._format_log_content(
            video_id, video_url, prompt, response, video_metadata, timestamp
        )
        
        # Write log file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        return str(filepath)

    def log_chat_chunk(self, video_id: str, video_url: str, prompt: str,
                       response: str, video_metadata: Optional[Dict[str, Any]] = None,
                       chunk_index: int = 0, start_offset: int = 0, end_offset: int = 0) -> str:
        """
        Log a chat conversation for a video chunk to a markdown file.

        Args:
            video_id: YouTube video ID
            video_url: Full YouTube URL
            prompt: The prompt sent to Gemini for the chunk
            response: The response received from Gemini for the chunk
            video_metadata: Optional video metadata
            chunk_index: Index of the video chunk
            start_offset: Start time of the chunk in seconds
            end_offset: End time of the chunk in seconds

        Returns:
            str: Path to the created log file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{video_id}_chunk_{chunk_index}_{timestamp}.md"
        filepath = self.log_directory / filename

        # Prepare log content
        log_content = self._format_chunk_log_content(
            video_id, video_url, prompt, response, video_metadata, timestamp,
            chunk_index, start_offset, end_offset
        )

        # Write log file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(log_content)

        return str(filepath)
    
    def _format_log_content(self, video_id: str, video_url: str, prompt: str,
                           response: str, video_metadata: Optional[Dict[str, Any]],
                           timestamp: str) -> str:
        """
        Format the chat log content as markdown.
        
        Args:
            video_id: YouTube video ID
            video_url: Full YouTube URL
            prompt: The prompt sent to Gemini
            response: The response received from Gemini
            video_metadata: Optional video metadata
            timestamp: Formatted timestamp
            
        Returns:
            str: Formatted markdown content
        """
        # Format timestamp for display
        display_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        content = f"""# Gemini Chat Log

## Session Information
- **Timestamp**: {display_timestamp}
- **Video ID**: {video_id}
- **Video URL**: {video_url}
"""
        
        # Add video metadata if available
        if video_metadata:
            content += f"""
## Video Metadata
- **Title**: {video_metadata.get('title', 'Unknown')}
- **Channel**: {video_metadata.get('channel', 'Unknown')}
- **Published**: {video_metadata.get('published_at', 'Unknown')}
- **Thumbnail**: {video_metadata.get('thumbnail_url', 'N/A')}
"""
        
        content += f"""
## Conversation

### User Prompt
```
{prompt}
```

### Gemini Response
{response}

---
*Log generated automatically by YouTube-Notion Integration*
"""

        return content

    def _format_chunk_log_content(self, video_id: str, video_url: str, prompt: str,
                                 response: str, video_metadata: Optional[Dict[str, Any]],
                                 timestamp: str, chunk_index: int, start_offset: int, end_offset: int) -> str:
        """
        Format the chat log content for a video chunk as markdown.
        """
        display_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = f"""# Gemini Chat Log (Chunk)

## Session Information
- **Timestamp**: {display_timestamp}
- **Video ID**: {video_id}
- **Video URL**: {video_url}

## Chunk Information
- **Chunk Index**: {chunk_index}
- **Start Offset**: {start_offset}s
- **End Offset**: {end_offset}s
"""

        if video_metadata:
            content += f"""
## Video Metadata
- **Title**: {video_metadata.get('title', 'Unknown')}
- **Channel**: {video_metadata.get('channel', 'Unknown')}
"""

        content += f"""
## Conversation

### User Prompt
```
{prompt}
```

### Gemini Response
{response}

---
*Log generated automatically by YouTube-Notion Integration*
"""
        
        return content
    
    def get_log_files(self, video_id: Optional[str] = None) -> list:
        """
        Get list of log files, optionally filtered by video ID.
        
        Args:
            video_id: Optional video ID to filter by
            
        Returns:
            list: List of log file paths
        """
        if not self.log_directory.exists():
            return []
        
        pattern = f"{video_id}_*.md" if video_id else "*.md"
        return list(self.log_directory.glob(pattern))
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """
        Clean up log files older than specified days.
        
        Args:
            days_to_keep: Number of days to keep logs (default: 30)
        """
        if not self.log_directory.exists():
            return
        
        cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
        
        for log_file in self.log_directory.glob("*.md"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
    
    def get_latest_log_path(self, video_id: Optional[str] = None) -> Optional[str]:
        """
        Get the path to the most recent main log file (excludes chunk logs).
        
        Args:
            video_id: Optional video ID to filter by
            
        Returns:
            Optional[str]: Path to the latest main log file, or None if no logs exist
        """
        log_files = self.get_log_files(video_id)
        
        if not log_files:
            return None
        
        # Filter out chunk logs (files containing "_chunk_")
        main_log_files = [f for f in log_files if "_chunk_" not in f.name]
        
        if not main_log_files:
            return None
        
        # Sort by modification time (newest first)
        latest_file = max(main_log_files, key=lambda f: f.stat().st_mtime)
        return str(latest_file)
    
    def get_chunk_log_paths(self, video_id: str) -> list:
        """
        Get paths to all chunk log files for a specific video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            list: List of chunk log file paths, sorted by chunk index
        """
        if not self.log_directory.exists():
            return []
        
        # Find all chunk log files for this video
        chunk_pattern = f"{video_id}_chunk_*.md"
        chunk_files = list(self.log_directory.glob(chunk_pattern))
        
        if not chunk_files:
            return []
        
        # Sort by chunk index (extract from filename)
        def extract_chunk_index(filepath):
            try:
                # Extract chunk index from filename like "video_id_chunk_0_timestamp.md"
                filename = filepath.stem
                parts = filename.split('_')
                chunk_idx = None
                for i, part in enumerate(parts):
                    if part == 'chunk' and i + 1 < len(parts):
                        chunk_idx = int(parts[i + 1])
                        break
                return chunk_idx if chunk_idx is not None else 0
            except (ValueError, IndexError):
                return 0
        
        chunk_files.sort(key=extract_chunk_index)
        return [str(f) for f in chunk_files]