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