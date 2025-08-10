"""
Test fixtures and sample data for web UI testing.

This module provides comprehensive test data for web UI components,
including sample queue items, API responses, and SSE events.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from src.youtube_notion.web.models import QueueItem, QueueStatus, ProcessingPhase


# Sample YouTube URLs for testing
SAMPLE_YOUTUBE_URLS = [
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://youtu.be/jNQXAC9IVRw",
    "https://www.youtube.com/watch?v=9bZkp7q19f0",
    "https://youtu.be/kJQP7kiw5Fk",
    "https://www.youtube.com/watch?v=L_jWHffIx5E",
]

# Sample video metadata
SAMPLE_VIDEO_METADATA = {
    "dQw4w9WgXcQ": {
        "title": "Rick Astley - Never Gonna Give You Up (Official Video)",
        "channel": "Rick Astley",
        "thumbnail_url": "https://img.youtube.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
        "duration": 212,
        "video_id": "dQw4w9WgXcQ"
    },
    "jNQXAC9IVRw": {
        "title": "Me at the zoo",
        "channel": "jawed",
        "thumbnail_url": "https://img.youtube.com/vi/jNQXAC9IVRw/maxresdefault.jpg",
        "duration": 19,
        "video_id": "jNQXAC9IVRw"
    },
    "9bZkp7q19f0": {
        "title": "PSY - GANGNAM STYLE(강남스타일) M/V",
        "channel": "officialpsy",
        "thumbnail_url": "https://img.youtube.com/vi/9bZkp7q19f0/maxresdefault.jpg",
        "duration": 253,
        "video_id": "9bZkp7q19f0"
    },
    "kJQP7kiw5Fk": {
        "title": "Despacito",
        "channel": "Luis Fonsi",
        "thumbnail_url": "https://img.youtube.com/vi/kJQP7kiw5Fk/maxresdefault.jpg",
        "duration": 281,
        "video_id": "kJQP7kiw5Fk"
    },
    "L_jWHffIx5E": {
        "title": "See You Again (feat. Charlie Puth)",
        "channel": "Wiz Khalifa",
        "thumbnail_url": "https://img.youtube.com/vi/L_jWHffIx5E/maxresdefault.jpg",
        "duration": 229,
        "video_id": "L_jWHffIx5E"
    }
}

# Sample custom prompts
SAMPLE_CUSTOM_PROMPTS = [
    "Summarize this video with focus on technical details",
    "Create a brief overview highlighting key points",
    "Provide a detailed analysis of the main concepts",
    "Extract actionable insights from this content",
    None  # No custom prompt
]

# Sample error messages for testing error handling
SAMPLE_ERROR_MESSAGES = {
    "invalid_url": [
        "Invalid URL format",
        "URL is not valid",
        "Please enter a valid YouTube URL",
        "Invalid YouTube URL provided"
    ],
    "network_error": [
        "Network connection failed",
        "Connection timeout",
        "Failed to fetch",
        "Network error occurred"
    ],
    "video_not_found": [
        "Video not found",
        "Video not available",
        "Video may be private or deleted",
        "Unable to access video"
    ],
    "processing_error": [
        "Processing failed",
        "AI processing error",
        "Summary generation failed",
        "Processing error occurred"
    ],
    "storage_error": [
        "Storage operation failed",
        "Failed to save to Notion",
        "Database error",
        "Storage error occurred"
    ],
    "queue_full": [
        "Queue is full",
        "Queue is full (max 100 items)",
        "Maximum queue size reached",
        "Queue capacity exceeded"
    ],
    "server_error": [
        "Internal server error",
        "Server error occurred",
        "Unexpected server error",
        "Server temporarily unavailable"
    ]
}


def create_sample_queue_item(
    item_id: str = "test-item-1",
    url: str = None,
    status: QueueStatus = QueueStatus.TODO,
    title: str = None,
    custom_prompt: str = None,
    created_minutes_ago: int = 0,
    started_minutes_ago: int = None,
    completed_minutes_ago: int = None,
    error_message: str = None,
    current_phase: str = None,
    current_chunk: int = None,
    total_chunks: int = None,
    chat_log_path: str = None,
    chunk_logs: List[str] = None
) -> QueueItem:
    """
    Create a sample queue item for testing.
    
    Args:
        item_id: Unique identifier for the item
        url: YouTube URL (defaults to first sample URL)
        status: Queue status
        title: Video title (auto-generated from URL if not provided)
        custom_prompt: Custom prompt for processing
        created_minutes_ago: Minutes ago when item was created
        started_minutes_ago: Minutes ago when processing started
        completed_minutes_ago: Minutes ago when processing completed
        error_message: Error message if processing failed
        current_phase: Current processing phase
        current_chunk: Current chunk being processed
        total_chunks: Total number of chunks
        chat_log_path: Path to chat log file
        chunk_logs: List of chunk log file paths
        
    Returns:
        QueueItem: Configured queue item for testing
    """
    if url is None:
        url = SAMPLE_YOUTUBE_URLS[0]
    
    # Extract video ID for metadata lookup
    video_id = url.split('/')[-1].split('?')[0].split('&')[0]
    if 'watch?v=' in url:
        video_id = url.split('watch?v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[1].split('?')[0]
    
    # Get metadata if available
    metadata = SAMPLE_VIDEO_METADATA.get(video_id, {})
    if title is None:
        title = metadata.get('title', f'Sample Video {item_id}')
    
    # Calculate timestamps
    now = datetime.now()
    created_at = now - timedelta(minutes=created_minutes_ago)
    started_at = None
    completed_at = None
    
    if started_minutes_ago is not None:
        started_at = now - timedelta(minutes=started_minutes_ago)
    
    if completed_minutes_ago is not None:
        completed_at = now - timedelta(minutes=completed_minutes_ago)
    
    # Set default chat log path if completed
    if chat_log_path is None and status in [QueueStatus.COMPLETED, QueueStatus.FAILED]:
        chat_log_path = f"chat_logs/{video_id}_{item_id}.md"
    
    # Set default chunk logs for chunked videos
    if chunk_logs is None and total_chunks and total_chunks > 1:
        chunk_logs = [f"chat_logs/{video_id}_{item_id}_chunk_{i}.md" for i in range(total_chunks)]
    elif chunk_logs is None:
        chunk_logs = []
    
    return QueueItem(
        id=item_id,
        url=url,
        custom_prompt=custom_prompt,
        status=status,
        title=title,
        thumbnail_url=metadata.get('thumbnail_url'),
        channel=metadata.get('channel'),
        created_at=created_at,
        started_at=started_at,
        completed_at=completed_at,
        error_message=error_message,
        chat_log_path=chat_log_path,
        chunk_logs=chunk_logs,
        current_phase=current_phase,
        current_chunk=current_chunk,
        total_chunks=total_chunks
    )


def create_sample_queue_status() -> Dict[str, List[QueueItem]]:
    """
    Create a sample queue status with items in different states.
    
    Returns:
        Dict[str, List[QueueItem]]: Queue status organized by state
    """
    return {
        'todo': [
            create_sample_queue_item(
                item_id="todo-1",
                url=SAMPLE_YOUTUBE_URLS[0],
                status=QueueStatus.TODO,
                created_minutes_ago=5
            ),
            create_sample_queue_item(
                item_id="todo-2",
                url=SAMPLE_YOUTUBE_URLS[1],
                status=QueueStatus.TODO,
                custom_prompt=SAMPLE_CUSTOM_PROMPTS[0],
                created_minutes_ago=3
            )
        ],
        'in_progress': [
            create_sample_queue_item(
                item_id="progress-1",
                url=SAMPLE_YOUTUBE_URLS[2],
                status=QueueStatus.IN_PROGRESS,
                created_minutes_ago=10,
                started_minutes_ago=8,
                current_phase=ProcessingPhase.SUMMARY_GENERATION.value
            )
        ],
        'completed': [
            create_sample_queue_item(
                item_id="completed-1",
                url=SAMPLE_YOUTUBE_URLS[3],
                status=QueueStatus.COMPLETED,
                created_minutes_ago=30,
                started_minutes_ago=28,
                completed_minutes_ago=25
            ),
            create_sample_queue_item(
                item_id="completed-2",
                url=SAMPLE_YOUTUBE_URLS[4],
                status=QueueStatus.COMPLETED,
                created_minutes_ago=45,
                started_minutes_ago=43,
                completed_minutes_ago=35,
                total_chunks=3,
                current_chunk=3
            )
        ],
        'failed': [
            create_sample_queue_item(
                item_id="failed-1",
                url="https://youtu.be/invalid123",
                status=QueueStatus.FAILED,
                title="Invalid Video",
                created_minutes_ago=20,
                started_minutes_ago=18,
                completed_minutes_ago=17,
                error_message="Video not found"
            )
        ]
    }


def create_sample_sse_events() -> List[Dict[str, Any]]:
    """
    Create sample Server-Sent Events for testing.
    
    Returns:
        List[Dict[str, Any]]: List of SSE event data
    """
    return [
        {
            "type": "queue_status",
            "data": create_sample_queue_status(),
            "timestamp": datetime.now().isoformat()
        },
        {
            "type": "status_change",
            "data": {
                "item_id": "test-item-1",
                "item": create_sample_queue_item(
                    item_id="test-item-1",
                    status=QueueStatus.IN_PROGRESS,
                    current_phase=ProcessingPhase.METADATA_EXTRACTION.value
                ).__dict__
            },
            "timestamp": datetime.now().isoformat()
        },
        {
            "type": "heartbeat",
            "timestamp": datetime.now().isoformat()
        },
        {
            "type": "error",
            "error": "Connection temporarily lost",
            "timestamp": datetime.now().isoformat()
        }
    ]


def create_sample_api_responses() -> Dict[str, Dict[str, Any]]:
    """
    Create sample API responses for testing.
    
    Returns:
        Dict[str, Dict[str, Any]]: Sample API responses by endpoint
    """
    return {
        "add_url_success": {
            "success": True,
            "item_id": "new-item-123"
        },
        "add_url_error": {
            "success": False,
            "error": "Invalid YouTube URL format"
        },
        "queue_status": {
            "todo": [item.__dict__ for item in create_sample_queue_status()['todo']],
            "in_progress": [item.__dict__ for item in create_sample_queue_status()['in_progress']],
            "completed": [item.__dict__ for item in create_sample_queue_status()['completed']],
            "failed": [item.__dict__ for item in create_sample_queue_status()['failed']]
        },
        "chat_log": {
            "item_id": "completed-1",
            "url": SAMPLE_YOUTUBE_URLS[3],
            "title": "Sample Video",
            "chat_log": "# Video Summary\n\nThis is a sample chat log for testing purposes.\n\n## Key Points\n- [2:30] First important point\n- [5:45] Second key insight\n- [8:15] Final conclusion",
            "created_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
            "completed_at": (datetime.now() - timedelta(minutes=25)).isoformat()
        },
        "chat_log_chunk": {
            "item_id": "completed-2",
            "url": SAMPLE_YOUTUBE_URLS[4],
            "title": "Long Video",
            "chat_log": "# Video Summary - Chunk 1\n\nThis is chunk 1 of a multi-part video summary.\n\n## Key Points\n- [2:30] Introduction\n- [5:45] First main topic",
            "chunk_index": 0,
            "is_chunk_log": True,
            "created_at": (datetime.now() - timedelta(minutes=45)).isoformat(),
            "completed_at": (datetime.now() - timedelta(minutes=35)).isoformat()
        },
        "health_check": {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "queue_stats": {
                "total_items": 6,
                "todo": 2,
                "in_progress": 1,
                "completed": 2,
                "failed": 1
            }
        }
    }


def create_sample_error_scenarios() -> Dict[str, Dict[str, Any]]:
    """
    Create sample error scenarios for testing error handling.
    
    Returns:
        Dict[str, Dict[str, Any]]: Error scenarios by type
    """
    return {
        "network_error": {
            "error": "Network connection failed",
            "status_code": None,
            "retry_after": 30
        },
        "invalid_url": {
            "error": "Invalid YouTube URL format",
            "status_code": 400,
            "details": "URL must be a valid YouTube link"
        },
        "queue_full": {
            "error": "Queue is full (max 100 items)",
            "status_code": 429,
            "retry_after": 60
        },
        "server_error": {
            "error": "Internal server error",
            "status_code": 500,
            "details": "Unexpected error occurred"
        },
        "video_not_found": {
            "error": "Video not found",
            "status_code": 404,
            "details": "Video may be private or deleted"
        },
        "processing_failed": {
            "error": "AI processing failed",
            "status_code": 422,
            "details": "Unable to generate summary"
        }
    }


def create_sample_chat_logs() -> Dict[str, str]:
    """
    Create sample chat log content for testing.
    
    Returns:
        Dict[str, str]: Chat log content by video ID
    """
    return {
        "dQw4w9WgXcQ": """# Rick Astley - Never Gonna Give You Up (Official Video)

## Summary

This is the official music video for Rick Astley's classic hit "Never Gonna Give You Up" from 1987.

## Key Points

- [0:00] Classic 80s music video opening
- [0:45] Rick Astley's distinctive vocals begin
- [1:30] Iconic dance moves and choreography
- [2:15] Memorable chorus section
- [3:00] Video concludes with classic 80s styling

## Analysis

The video represents a quintessential example of 1980s pop music and has become an internet phenomenon known as "Rickrolling."
""",
        "jNQXAC9IVRw": """# Me at the zoo

## Summary

The first video ever uploaded to YouTube, featuring co-founder Jawed Karim at the San Diego Zoo.

## Key Points

- [0:00] Historic first YouTube video
- [0:05] Jawed Karim introduces himself
- [0:10] Comments about elephant trunks
- [0:15] Simple, unedited format

## Historical Significance

This 19-second video marked the beginning of the YouTube era and user-generated content revolution.
""",
        "chunked_video_chunk_0": """# Long Video Analysis - Chunk 1 (0:00-45:00)

## Summary

This is the first part of a comprehensive analysis of a long-form video content.

## Key Points

- [2:30] Introduction to main topic
- [8:15] First major concept explained
- [15:45] Supporting evidence presented
- [25:30] Initial conclusions drawn
- [35:00] Transition to next section
- [42:15] Setup for continuation

## Context for Next Chunk

The video continues with deeper analysis of the concepts introduced in this section.
""",
        "chunked_video_chunk_1": """# Long Video Analysis - Chunk 2 (40:00-85:00)

## Summary

Continuation of the comprehensive video analysis, building on concepts from the first chunk.

## Key Points

- [42:30] Recap of previous section
- [48:15] Deep dive into advanced concepts
- [55:45] Case studies and examples
- [65:30] Practical applications discussed
- [75:00] Integration with earlier points
- [82:15] Preparation for final section

## Context

This middle section bridges the introductory concepts with the final conclusions.
"""
    }


# Convenience functions for creating test data

def get_sample_queue_item_by_status(status: QueueStatus) -> QueueItem:
    """Get a sample queue item with the specified status."""
    queue_status = create_sample_queue_status()
    status_key = status.value.replace('_', '')  # Convert IN_PROGRESS to inprogress
    if status_key == 'inprogress':
        status_key = 'in_progress'
    
    items = queue_status.get(status_key, [])
    return items[0] if items else create_sample_queue_item(status=status)


def get_sample_error_message(error_type: str) -> str:
    """Get a sample error message of the specified type."""
    messages = SAMPLE_ERROR_MESSAGES.get(error_type, ["Unknown error"])
    return messages[0]


def get_sample_youtube_url(index: int = 0) -> str:
    """Get a sample YouTube URL by index."""
    return SAMPLE_YOUTUBE_URLS[index % len(SAMPLE_YOUTUBE_URLS)]


def get_sample_video_metadata(url: str) -> Dict[str, Any]:
    """Get sample metadata for a YouTube URL."""
    video_id = url.split('/')[-1].split('?')[0].split('&')[0]
    if 'watch?v=' in url:
        video_id = url.split('watch?v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[1].split('?')[0]
    
    return SAMPLE_VIDEO_METADATA.get(video_id, {
        "title": f"Sample Video {video_id}",
        "channel": "Sample Channel",
        "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg",
        "duration": 180,
        "video_id": video_id
    })