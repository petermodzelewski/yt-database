# Chat Logs

This directory contains conversation logs between the YouTube-Notion Integration and Google Gemini AI.

## File Format

Chat logs are saved as markdown files with the naming convention:
```
<youtube_video_id>_<timestamp>.md
```

For example: `dQw4w9WgXcQ_20250803_101559.md`

## Log Content

Each log file contains:

- **Session Information**: Timestamp, video ID, and video URL
- **Video Metadata**: Title, channel, publication date, and thumbnail URL
- **Conversation**: The complete prompt sent to Gemini and the AI's response

## Purpose

These logs are useful for:
- Reviewing AI-generated summaries
- Debugging prompt effectiveness
- Tracking processing history
- Quality assurance and improvement

## Privacy Note

These files are automatically excluded from git commits via `.gitignore` to protect any sensitive information that might be contained in video content or AI responses.

## Cleanup

The system includes automatic cleanup functionality to remove logs older than 30 days. You can also manually delete old logs as needed.