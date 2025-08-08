"""
Unit tests for web UI data models and enumerations.

Tests cover data model validation, serialization, enum values,
and Pydantic model conversion functionality.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from src.youtube_notion.web.models import (
    QueueStatus,
    ProcessingPhase,
    QueueItem,
    AddUrlRequest,
    AddUrlResponse,
    QueueItemResponse,
    QueueStatusResponse,
    ErrorResponse,
    ErrorCodes
)


class TestQueueStatus:
    """Test cases for QueueStatus enumeration."""
    
    def test_queue_status_values(self):
        """Test that QueueStatus enum has correct values."""
        assert QueueStatus.TODO.value == "todo"
        assert QueueStatus.IN_PROGRESS.value == "in_progress"
        assert QueueStatus.COMPLETED.value == "completed"
        assert QueueStatus.FAILED.value == "failed"
    
    def test_queue_status_members(self):
        """Test that QueueStatus has all expected members."""
        expected_members = {"TODO", "IN_PROGRESS", "COMPLETED", "FAILED"}
        actual_members = {member.name for member in QueueStatus}
        assert actual_members == expected_members


class TestProcessingPhase:
    """Test cases for ProcessingPhase enumeration."""
    
    def test_processing_phase_values(self):
        """Test that ProcessingPhase enum has correct values."""
        assert ProcessingPhase.METADATA_EXTRACTION.value == "Extracting metadata"
        assert ProcessingPhase.SUMMARY_GENERATION.value == "Generating summary"
        assert ProcessingPhase.CHUNK_PROCESSING.value == "Processing chunk"
        assert ProcessingPhase.NOTION_UPLOAD.value == "Uploading to Notion"
    
    def test_processing_phase_members(self):
        """Test that ProcessingPhase has all expected members."""
        expected_members = {
            "METADATA_EXTRACTION", 
            "SUMMARY_GENERATION", 
            "CHUNK_PROCESSING", 
            "NOTION_UPLOAD"
        }
        actual_members = {member.name for member in ProcessingPhase}
        assert actual_members == expected_members


class TestQueueItem:
    """Test cases for QueueItem dataclass."""
    
    def test_queue_item_creation_minimal(self):
        """Test creating QueueItem with minimal required fields."""
        item = QueueItem(id="test-1", url="https://youtu.be/test123")
        
        assert item.id == "test-1"
        assert item.url == "https://youtu.be/test123"
        assert item.custom_prompt is None
        assert item.status == QueueStatus.TODO
        assert item.title is None
        assert item.thumbnail_url is None
        assert item.channel is None
        assert isinstance(item.created_at, datetime)
        assert item.started_at is None
        assert item.completed_at is None
        assert item.error_message is None
        assert item.chat_log_path is None
        assert item.chunk_logs == []
        assert item.current_phase is None
        assert item.current_chunk is None
        assert item.total_chunks is None
    
    def test_queue_item_creation_full(self):
        """Test creating QueueItem with all fields populated."""
        created_time = datetime.now()
        started_time = datetime.now()
        completed_time = datetime.now()
        
        item = QueueItem(
            id="test-2",
            url="https://youtu.be/test456",
            custom_prompt="Custom prompt",
            status=QueueStatus.COMPLETED,
            title="Test Video",
            thumbnail_url="https://img.youtube.com/vi/test456/maxresdefault.jpg",
            channel="Test Channel",
            created_at=created_time,
            started_at=started_time,
            completed_at=completed_time,
            error_message=None,
            chat_log_path="/path/to/chat.log",
            chunk_logs=["chunk1.log", "chunk2.log"],
            current_phase="Completed",
            current_chunk=2,
            total_chunks=2
        )
        
        assert item.id == "test-2"
        assert item.url == "https://youtu.be/test456"
        assert item.custom_prompt == "Custom prompt"
        assert item.status == QueueStatus.COMPLETED
        assert item.title == "Test Video"
        assert item.thumbnail_url == "https://img.youtube.com/vi/test456/maxresdefault.jpg"
        assert item.channel == "Test Channel"
        assert item.created_at == created_time
        assert item.started_at == started_time
        assert item.completed_at == completed_time
        assert item.error_message is None
        assert item.chat_log_path == "/path/to/chat.log"
        assert item.chunk_logs == ["chunk1.log", "chunk2.log"]
        assert item.current_phase == "Completed"
        assert item.current_chunk == 2
        assert item.total_chunks == 2
    
    def test_queue_item_default_factory(self):
        """Test that default factories work correctly."""
        item1 = QueueItem(id="test-1", url="https://youtu.be/test1")
        item2 = QueueItem(id="test-2", url="https://youtu.be/test2")
        
        # Each item should have its own list instance
        item1.chunk_logs.append("log1")
        assert item1.chunk_logs == ["log1"]
        assert item2.chunk_logs == []
        
        # Created times should be different (or very close)
        assert isinstance(item1.created_at, datetime)
        assert isinstance(item2.created_at, datetime)


class TestAddUrlRequest:
    """Test cases for AddUrlRequest Pydantic model."""
    
    def test_add_url_request_valid(self):
        """Test creating AddUrlRequest with valid data."""
        request = AddUrlRequest(url="https://youtu.be/test123")
        assert str(request.url) == "https://youtu.be/test123"
        assert request.custom_prompt is None
    
    def test_add_url_request_with_prompt(self):
        """Test creating AddUrlRequest with custom prompt."""
        request = AddUrlRequest(
            url="https://youtu.be/test123",
            custom_prompt="Custom prompt"
        )
        assert str(request.url) == "https://youtu.be/test123"
        assert request.custom_prompt == "Custom prompt"
    
    def test_add_url_request_invalid_url(self):
        """Test that invalid URLs raise ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            AddUrlRequest(url="not-a-url")
        
        assert "url" in str(exc_info.value)
    
    def test_add_url_request_serialization(self):
        """Test JSON serialization of AddUrlRequest."""
        request = AddUrlRequest(
            url="https://youtu.be/test123",
            custom_prompt="Test prompt"
        )
        data = request.model_dump()
        
        # Pydantic HttpUrl serializes as HttpUrl object, convert to string for comparison
        assert str(data["url"]) == "https://youtu.be/test123"
        assert data["custom_prompt"] == "Test prompt"


class TestAddUrlResponse:
    """Test cases for AddUrlResponse Pydantic model."""
    
    def test_add_url_response_success(self):
        """Test creating successful AddUrlResponse."""
        response = AddUrlResponse(success=True, item_id="test-123")
        assert response.success is True
        assert response.item_id == "test-123"
        assert response.error is None
    
    def test_add_url_response_error(self):
        """Test creating error AddUrlResponse."""
        response = AddUrlResponse(success=False, error="Invalid URL")
        assert response.success is False
        assert response.item_id is None
        assert response.error == "Invalid URL"
    
    def test_add_url_response_serialization(self):
        """Test JSON serialization of AddUrlResponse."""
        response = AddUrlResponse(success=True, item_id="test-123")
        data = response.model_dump()
        
        assert data["success"] is True
        assert data["item_id"] == "test-123"
        assert data["error"] is None


class TestQueueItemResponse:
    """Test cases for QueueItemResponse Pydantic model."""
    
    def test_queue_item_response_creation(self):
        """Test creating QueueItemResponse directly."""
        created_time = datetime.now()
        
        response = QueueItemResponse(
            id="test-1",
            url="https://youtu.be/test123",
            custom_prompt=None,
            status="todo",
            title="Test Video",
            thumbnail_url="https://img.youtube.com/vi/test123/maxresdefault.jpg",
            channel="Test Channel",
            duration=300,
            created_at=created_time,
            started_at=None,
            completed_at=None,
            error_message=None,
            chat_log_path=None,
            chunk_logs=[],
            current_phase=None,
            current_chunk=None,
            total_chunks=None
        )
        
        assert response.id == "test-1"
        assert response.url == "https://youtu.be/test123"
        assert response.status == "todo"
        assert response.title == "Test Video"
        assert response.created_at == created_time
    
    def test_from_queue_item_conversion(self):
        """Test converting QueueItem to QueueItemResponse."""
        queue_item = QueueItem(
            id="test-2",
            url="https://youtu.be/test456",
            custom_prompt="Custom prompt",
            status=QueueStatus.IN_PROGRESS,
            title="Test Video 2",
            thumbnail_url="https://img.youtube.com/vi/test456/maxresdefault.jpg",
            channel="Test Channel 2",
            chunk_logs=["chunk1.log"],
            current_phase="Processing",
            current_chunk=1,
            total_chunks=3
        )
        
        response = QueueItemResponse.from_queue_item(queue_item)
        
        assert response.id == "test-2"
        assert response.url == "https://youtu.be/test456"
        assert response.custom_prompt == "Custom prompt"
        assert response.status == "in_progress"  # Enum value converted to string
        assert response.title == "Test Video 2"
        assert response.thumbnail_url == "https://img.youtube.com/vi/test456/maxresdefault.jpg"
        assert response.channel == "Test Channel 2"
        assert response.chunk_logs == ["chunk1.log"]
        assert response.current_phase == "Processing"
        assert response.current_chunk == 1
        assert response.total_chunks == 3
    
    def test_queue_item_response_serialization(self):
        """Test JSON serialization of QueueItemResponse."""
        created_time = datetime.now()
        response = QueueItemResponse(
            id="test-1",
            url="https://youtu.be/test123",
            custom_prompt=None,
            status="todo",
            title="Test Video",
            thumbnail_url=None,
            channel=None,
            duration=None,
            created_at=created_time,
            started_at=None,
            completed_at=None,
            error_message=None,
            chat_log_path=None,
            chunk_logs=[],
            current_phase=None,
            current_chunk=None,
            total_chunks=None
        )
        
        data = response.model_dump()
        assert data["id"] == "test-1"
        assert data["status"] == "todo"
        assert data["chunk_logs"] == []


class TestQueueStatusResponse:
    """Test cases for QueueStatusResponse Pydantic model."""
    
    def test_queue_status_response_creation(self):
        """Test creating QueueStatusResponse with all columns."""
        todo_item = QueueItemResponse(
            id="todo-1", url="https://youtu.be/todo", custom_prompt=None,
            status="todo", title=None, thumbnail_url=None, channel=None,
            duration=None, created_at=datetime.now(), started_at=None, completed_at=None,
            error_message=None, chat_log_path=None, chunk_logs=[],
            current_phase=None, current_chunk=None, total_chunks=None
        )
        
        in_progress_item = QueueItemResponse(
            id="progress-1", url="https://youtu.be/progress", custom_prompt=None,
            status="in_progress", title=None, thumbnail_url=None, channel=None,
            duration=None, created_at=datetime.now(), started_at=datetime.now(), completed_at=None,
            error_message=None, chat_log_path=None, chunk_logs=[],
            current_phase="Processing", current_chunk=None, total_chunks=None
        )
        
        response = QueueStatusResponse(
            todo=[todo_item],
            in_progress=[in_progress_item],
            completed=[],
            failed=[]
        )
        
        assert len(response.todo) == 1
        assert len(response.in_progress) == 1
        assert len(response.completed) == 0
        assert len(response.failed) == 0
        assert response.todo[0].id == "todo-1"
        assert response.in_progress[0].id == "progress-1"
    
    def test_queue_status_response_serialization(self):
        """Test JSON serialization of QueueStatusResponse."""
        response = QueueStatusResponse(
            todo=[],
            in_progress=[],
            completed=[],
            failed=[]
        )
        
        data = response.model_dump()
        assert data["todo"] == []
        assert data["in_progress"] == []
        assert data["completed"] == []
        assert data["failed"] == []


class TestErrorResponse:
    """Test cases for ErrorResponse Pydantic model."""
    
    def test_error_response_creation(self):
        """Test creating ErrorResponse with required fields."""
        response = ErrorResponse(
            error="Test error",
            error_code=ErrorCodes.INVALID_URL
        )
        
        assert response.error == "Test error"
        assert response.details is None
        assert response.error_code == ErrorCodes.INVALID_URL
        assert isinstance(response.timestamp, datetime)
    
    def test_error_response_with_details(self):
        """Test creating ErrorResponse with details."""
        response = ErrorResponse(
            error="Processing failed",
            details="Video not found",
            error_code=ErrorCodes.PROCESSING_FAILED
        )
        
        assert response.error == "Processing failed"
        assert response.details == "Video not found"
        assert response.error_code == ErrorCodes.PROCESSING_FAILED
    
    def test_error_response_serialization(self):
        """Test JSON serialization of ErrorResponse."""
        response = ErrorResponse(
            error="Test error",
            error_code=ErrorCodes.SERVER_ERROR
        )
        
        data = response.model_dump()
        assert data["error"] == "Test error"
        assert data["error_code"] == ErrorCodes.SERVER_ERROR
        assert "timestamp" in data


class TestErrorCodes:
    """Test cases for ErrorCodes constants."""
    
    def test_error_codes_values(self):
        """Test that ErrorCodes has correct constant values."""
        assert ErrorCodes.INVALID_URL == "INVALID_URL"
        assert ErrorCodes.PROCESSING_FAILED == "PROCESSING_FAILED"
        assert ErrorCodes.QUEUE_FULL == "QUEUE_FULL"
        assert ErrorCodes.SERVER_ERROR == "SERVER_ERROR"
        assert ErrorCodes.ITEM_NOT_FOUND == "ITEM_NOT_FOUND"