"""
Data models and enumerations for the web UI queue system.

This module defines the core data structures used for queue management,
including status enumerations, processing phases, and the QueueItem model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, HttpUrl


class QueueStatus(Enum):
    """Enumeration for queue item status."""
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ProcessingPhase(Enum):
    """Enumeration for video processing phases."""
    METADATA_EXTRACTION = "Extracting metadata"
    SUMMARY_GENERATION = "Generating summary"
    CHUNK_PROCESSING = "Processing chunk"
    NOTION_UPLOAD = "Uploading to Notion"


@dataclass
class QueueItem:
    """
    Data model for queue items with status tracking.
    
    Represents a video processing task in the queue with all necessary
    metadata and status information for tracking progress.
    """
    id: str
    url: str
    custom_prompt: Optional[str] = None
    status: QueueStatus = QueueStatus.TODO
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    channel: Optional[str] = None
    duration: Optional[int] = None  # Duration in seconds
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    chat_log_path: Optional[str] = None
    chunk_logs: List[str] = field(default_factory=list)
    current_phase: Optional[str] = None
    current_chunk: Optional[int] = None
    total_chunks: Optional[int] = None


# Pydantic models for API requests and responses

class AddUrlRequest(BaseModel):
    """Request model for adding URLs to the queue."""
    url: HttpUrl
    custom_prompt: Optional[str] = None


class AddUrlResponse(BaseModel):
    """Response model for URL addition requests."""
    success: bool
    item_id: Optional[str] = None
    error: Optional[str] = None


class QueueItemResponse(BaseModel):
    """Pydantic model for QueueItem serialization in API responses."""
    id: str
    url: str
    custom_prompt: Optional[str]
    status: str  # QueueStatus enum value
    title: Optional[str]
    thumbnail_url: Optional[str]
    channel: Optional[str]
    duration: Optional[int]  # Duration in seconds
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    chat_log_path: Optional[str]
    chunk_logs: List[str]
    current_phase: Optional[str]
    current_chunk: Optional[int]
    total_chunks: Optional[int]

    @classmethod
    def from_queue_item(cls, item: QueueItem) -> 'QueueItemResponse':
        """Convert a QueueItem dataclass to a Pydantic model."""
        return cls(
            id=item.id,
            url=item.url,
            custom_prompt=item.custom_prompt,
            status=item.status.value,
            title=item.title,
            thumbnail_url=item.thumbnail_url,
            channel=item.channel,
            duration=item.duration,
            created_at=item.created_at,
            started_at=item.started_at,
            completed_at=item.completed_at,
            error_message=item.error_message,
            chat_log_path=item.chat_log_path,
            chunk_logs=item.chunk_logs,
            current_phase=item.current_phase,
            current_chunk=item.current_chunk,
            total_chunks=item.total_chunks
        )


class QueueStatusResponse(BaseModel):
    """Response model for queue status requests."""
    todo: List[QueueItemResponse]
    in_progress: List[QueueItemResponse]
    completed: List[QueueItemResponse]
    failed: List[QueueItemResponse]


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    details: Optional[str] = None
    error_code: str
    timestamp: datetime = field(default_factory=datetime.now)


class ErrorCodes:
    """Constants for error codes used in API responses."""
    INVALID_URL = "INVALID_URL"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    QUEUE_FULL = "QUEUE_FULL"
    SERVER_ERROR = "SERVER_ERROR"
    ITEM_NOT_FOUND = "ITEM_NOT_FOUND"