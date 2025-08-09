"""
Unit tests for the FastAPI web server.

This module tests the WebServer class and its API endpoints using FastAPI's
TestClient for isolated testing without external dependencies.
"""

import pytest
import asyncio
import json
import threading
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
import httpx

from src.youtube_notion.web.server import WebServer
from src.youtube_notion.web.config import WebServerConfig


class TestWebServerAPIEndpoints:
    """Test WebServer API endpoints using TestClient."""
    
    @pytest.fixture
    def mock_queue_manager(self):
        """Create a mock queue manager for testing."""
        mock = Mock()
        mock.enqueue = Mock()
        mock.get_queue_status = Mock()
        mock.get_item_status = Mock()
        mock.add_status_listener = Mock()
        mock.remove_status_listener = Mock()
        mock.start_processing = Mock()
        mock.stop_processing = Mock()
        mock.get_statistics = Mock()
        return mock
    
    @pytest.fixture
    def test_client(self, mock_queue_manager):
        """Create a test client with mock queue manager."""
        config = WebServerConfig(debug=True)
        server = WebServer(mock_queue_manager, config)
        return TestClient(server.app)
    
    def test_add_url_endpoint_success(self, test_client, mock_queue_manager):
        """Test successful URL addition to queue."""
        # Setup mock to return item ID
        mock_queue_manager.enqueue.return_value = "test-item-123"
        
        response = test_client.post(
            "/api/queue",
            json={
                "url": "https://youtu.be/test123",
                "custom_prompt": "Test prompt"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["item_id"] == "test-item-123"
        assert data["error"] is None
        
        # Verify queue manager was called
        mock_queue_manager.enqueue.assert_called_once_with("https://youtu.be/test123", "Test prompt")
    
    def test_add_url_endpoint_invalid_url(self, test_client, mock_queue_manager):
        """Test URL addition with invalid URL format."""
        response = test_client.post(
            "/api/queue",
            json={
                "url": "not-a-valid-url"
            }
        )
        
        assert response.status_code == 422  # Pydantic validation error
    
    def test_get_status_endpoint_success(self, test_client, mock_queue_manager):
        """Test successful queue status retrieval."""
        from src.youtube_notion.web.models import QueueItem, QueueStatus
        
        # Setup mock queue status
        test_item = QueueItem(
            id="test-123",
            url="https://youtu.be/test123",
            status=QueueStatus.TODO,
            title="Test Video"
        )
        mock_queue_manager.get_queue_status.return_value = {
            'todo': [test_item],
            'in_progress': [],
            'completed': [],
            'failed': []
        }
        
        response = test_client.get("/api/status")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["todo"]) == 1
        assert data["todo"][0]["id"] == "test-123"
        assert data["todo"][0]["url"] == "https://youtu.be/test123"
        assert data["todo"][0]["status"] == "todo"
    
    def test_get_chat_log_endpoint_success(self, test_client, mock_queue_manager):
        """Test successful chat log retrieval."""
        from src.youtube_notion.web.models import QueueItem, QueueStatus
        from datetime import datetime
        import tempfile
        from pathlib import Path
        
        # Create a temporary chat log file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Test chat log content")
            temp_path = f.name
        
        try:
            # Setup mock item with chat log
            test_item = QueueItem(
                id="test-123",
                url="https://youtu.be/test123",
                status=QueueStatus.COMPLETED,
                title="Test Video",
                chat_log_path=temp_path,
                completed_at=datetime.now()
            )
            mock_queue_manager.get_item_status.return_value = test_item
            
            response = test_client.get("/api/chat-log/test-123")
            
            assert response.status_code == 200
            data = response.json()
            assert data["item_id"] == "test-123"
            assert data["url"] == "https://youtu.be/test123"
            assert data["title"] == "Test Video"
            assert data["chat_log"] == "Test chat log content"
            assert "created_at" in data
            assert "completed_at" in data
        finally:
            # Clean up temp file
            Path(temp_path).unlink(missing_ok=True)
    
    def test_get_chat_log_endpoint_item_not_found(self, test_client, mock_queue_manager):
        """Test chat log retrieval for non-existent item."""
        mock_queue_manager.get_item_status.return_value = None
        
        response = test_client.get("/api/chat-log/nonexistent")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_chat_log_endpoint_chunk_success(self, test_client, mock_queue_manager):
        """Test successful chunk chat log retrieval."""
        from src.youtube_notion.web.models import QueueItem, QueueStatus
        from datetime import datetime
        import tempfile
        from pathlib import Path
        
        # Create temporary chunk log files
        chunk_files = []
        try:
            for i in range(2):
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=f'_chunk_{i}.txt') as f:
                    f.write(f"Chunk {i} chat log content")
                    chunk_files.append(f.name)
            
            # Setup mock item with chunk logs
            test_item = QueueItem(
                id="test-chunked",
                url="https://youtu.be/longvideo",
                status=QueueStatus.COMPLETED,
                title="Long Video",
                chunk_logs=chunk_files,
                completed_at=datetime.now()
            )
            mock_queue_manager.get_item_status.return_value = test_item
            
            # Test chunk 0
            response = test_client.get("/api/chat-log/test-chunked?chunk=0")
            
            assert response.status_code == 200
            data = response.json()
            assert data["item_id"] == "test-chunked"
            assert data["chat_log"] == "Chunk 0 chat log content"
            assert data["chunk_index"] == 0
            assert data["is_chunk_log"] is True
            
            # Test chunk 1
            response = test_client.get("/api/chat-log/test-chunked?chunk=1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["chat_log"] == "Chunk 1 chat log content"
            assert data["chunk_index"] == 1
            
        finally:
            # Clean up temp files
            for chunk_file in chunk_files:
                Path(chunk_file).unlink(missing_ok=True)
    
    def test_get_chat_log_endpoint_chunk_not_found(self, test_client, mock_queue_manager):
        """Test chunk chat log retrieval for non-existent chunk."""
        from src.youtube_notion.web.models import QueueItem, QueueStatus
        from datetime import datetime
        
        # Setup mock item without chunk logs
        test_item = QueueItem(
            id="test-no-chunks",
            url="https://youtu.be/shortvideo",
            status=QueueStatus.COMPLETED,
            title="Short Video",
            chunk_logs=[],
            completed_at=datetime.now()
        )
        mock_queue_manager.get_item_status.return_value = test_item
        
        response = test_client.get("/api/chat-log/test-no-chunks?chunk=0")
        
        assert response.status_code == 404
        assert "Chunk 0 not found" in response.json()["detail"]
    
    def test_get_chat_log_endpoint_chunk_out_of_range(self, test_client, mock_queue_manager):
        """Test chunk chat log retrieval for out-of-range chunk index."""
        from src.youtube_notion.web.models import QueueItem, QueueStatus
        from datetime import datetime
        import tempfile
        from pathlib import Path
        
        # Create one chunk file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='_chunk_0.txt') as f:
            f.write("Only chunk content")
            chunk_file = f.name
        
        try:
            # Setup mock item with one chunk log
            test_item = QueueItem(
                id="test-one-chunk",
                url="https://youtu.be/mediumvideo",
                status=QueueStatus.COMPLETED,
                title="Medium Video",
                chunk_logs=[chunk_file],
                completed_at=datetime.now()
            )
            mock_queue_manager.get_item_status.return_value = test_item
            
            # Request chunk 1 (out of range)
            response = test_client.get("/api/chat-log/test-one-chunk?chunk=1")
            
            assert response.status_code == 404
            assert "Chunk 1 not found" in response.json()["detail"]
            
        finally:
            # Clean up temp file
            Path(chunk_file).unlink(missing_ok=True)
    
    def test_health_check_endpoint(self, test_client, mock_queue_manager):
        """Test health check endpoint."""
        mock_queue_manager.get_statistics.return_value = {
            "total_items": 5,
            "completed": 3,
            "failed": 1,
            "in_progress": 1
        }
        
        response = test_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "queue_stats" in data
        assert data["queue_stats"]["total_items"] == 5
    
    def test_serve_index_with_static_files(self, test_client, mock_queue_manager):
        """Test serving index HTML file."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "<!DOCTYPE html>" in response.text
        assert "YouTube to Notion Queue" in response.text


class TestWebServerInitialization:
    """Test WebServer initialization and configuration."""
    
    def test_init_with_valid_queue_manager(self):
        """Test successful initialization with valid queue manager."""
        mock_queue_manager = Mock()
        config = WebServerConfig(port=8081, debug=True)
        
        server = WebServer(mock_queue_manager, config)
        
        assert server.queue_manager == mock_queue_manager
        assert server.config.port == 8081
        assert server.config.debug is True
        assert server.app is not None
        assert not server.is_running
    
    def test_init_without_queue_manager_raises_error(self):
        """Test that initialization without queue manager raises ConfigurationError."""
        from src.youtube_notion.utils.exceptions import ConfigurationError
        
        with pytest.raises(ConfigurationError, match="QueueManager is required"):
            WebServer(None)
    
    def test_fastapi_app_configuration(self):
        """Test that FastAPI app is properly configured."""
        mock_queue_manager = Mock()
        server = WebServer(mock_queue_manager)
        
        assert server.app.title == "YouTube-to-Notion Web UI"
        assert "Web interface for managing YouTube video processing queue" in server.app.description
        assert server.app.version == "1.0.0"


class TestWebServerLifecycle:
    """Test WebServer start/stop lifecycle."""
    
    def test_server_start_stop(self):
        """Test server start and stop functionality."""
        mock_queue_manager = Mock()
        config = WebServerConfig(port=8081)
        server = WebServer(mock_queue_manager, config)
        
        assert not server.is_running
        
        # Test that we can't start twice
        with patch.object(server, '_run_server'):
            server.start()
            assert server.is_running
            
            with pytest.raises(RuntimeError, match="already running"):
                server.start()
            
            # Test stop
            success = server.stop(timeout=1.0)
            assert success
            assert not server.is_running


class TestServerSentEvents:
    """Test Server-Sent Events functionality for real-time updates."""
    
    @pytest.fixture
    def mock_queue_manager(self):
        """Create a mock queue manager with SSE support."""
        from tests.fixtures.mock_implementations import MockQueueManager
        return MockQueueManager()
    
    @pytest.fixture
    def test_client(self, mock_queue_manager):
        """Create a test client with mock queue manager."""
        config = WebServerConfig(debug=True, sse_heartbeat_interval=1)
        server = WebServer(mock_queue_manager, config)
        return TestClient(server.app)
    
    @pytest.fixture
    def server(self, mock_queue_manager):
        """Create a web server instance for async testing."""
        config = WebServerConfig(debug=True, sse_heartbeat_interval=1)
        return WebServer(mock_queue_manager, config)
    
    def test_sse_endpoint_initial_status(self, test_client, mock_queue_manager):
        """Test SSE endpoint returns initial queue status."""
        from src.youtube_notion.web.models import QueueStatus
        
        # Add some mock items to the queue
        mock_queue_manager.add_mock_item("item-1", "https://youtu.be/test1", QueueStatus.TODO)
        mock_queue_manager.add_mock_item("item-2", "https://youtu.be/test2", QueueStatus.IN_PROGRESS)
        mock_queue_manager.add_mock_item("item-3", "https://youtu.be/test3", QueueStatus.COMPLETED)
        
        # Connect to SSE endpoint with test mode to get only initial status
        with test_client.stream("GET", "/events?test_mode=initial_only") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["connection"] == "keep-alive"
            
            # Read all content from the stream (should be just the initial event)
            content = response.read().decode('utf-8')
            
            # Parse the SSE event
            lines = content.strip().split('\n')
            data_line = next((line for line in lines if line.startswith("data: ")), None)
            assert data_line is not None
            
            event_data = json.loads(data_line[6:])  # Remove "data: " prefix
            assert event_data["type"] == "queue_status"
            assert "data" in event_data
            assert "timestamp" in event_data
            
            # Verify queue status structure
            queue_data = event_data["data"]
            assert len(queue_data["todo"]) == 1
            assert len(queue_data["in_progress"]) == 1
            assert len(queue_data["completed"]) == 1
            assert len(queue_data["failed"]) == 0
            
            assert queue_data["todo"][0]["id"] == "item-1"
            assert queue_data["in_progress"][0]["id"] == "item-2"
            assert queue_data["completed"][0]["id"] == "item-3"

    
    def test_sse_status_change_events(self, server, mock_queue_manager):
        """Test that SSE broadcasts status change events via listener."""
        from src.youtube_notion.web.models import QueueStatus
        
        # Get the registered listener
        assert len(mock_queue_manager.add_status_listener_calls) == 1
        listener = mock_queue_manager.add_status_listener_calls[0]
        
        # Create a mock item
        item = mock_queue_manager.add_mock_item(
            "test-item", 
            "https://youtu.be/test", 
            QueueStatus.TODO
        )
        
        # Track SSE connections before calling listener
        initial_connections = len(server._sse_connections)
        
        # Call the listener directly (simulating a status change)
        listener("test-item", item)
        
        # Verify the listener was called without errors
        # (The broadcast method should handle empty connections gracefully)
        assert len(server._sse_connections) == initial_connections
    

    

    
    def test_sse_error_handling(self, mock_queue_manager):
        """Test SSE error handling in broadcast method."""
        from src.youtube_notion.web.models import QueueStatus
        import asyncio
        
        config = WebServerConfig(debug=True, sse_heartbeat_interval=1)
        server = WebServer(mock_queue_manager, config)
        
        # Create a mock connection queue that will raise an exception
        failing_queue = asyncio.Queue()
        
        # Mock put_nowait to raise an exception
        def failing_put_nowait(data):
            raise Exception("Mock connection error")
        
        failing_queue.put_nowait = failing_put_nowait
        
        # Add the failing queue to connections
        server._sse_connections.append(failing_queue)
        
        # Create test event data
        event_data = {
            "type": "test_event",
            "data": {"test": "data"},
            "timestamp": "2023-01-01T00:00:00"
        }
        
        # This should not raise an exception - errors should be handled gracefully
        server._broadcast_sse_event(event_data)
        
        # The failing connection should be removed from the list
        assert len(server._sse_connections) == 0
    
    @pytest.mark.asyncio
    async def test_sse_event_serialization(self, server, mock_queue_manager):
        """Test proper SSE event serialization and formatting."""
        from src.youtube_notion.web.models import QueueStatus
        from datetime import datetime
        from httpx import AsyncClient, ASGITransport
        
        # Add an item with various metadata
        item = mock_queue_manager.add_mock_item(
            "test-item", 
            "https://youtu.be/test123", 
            QueueStatus.TODO
        )
        item.title = "Test Video Title"
        item.thumbnail_url = "https://img.youtube.com/vi/test123/maxresdefault.jpg"
        item.channel = "Test Channel"
        item.custom_prompt = "Custom test prompt"
        
        # Use the synchronous test client for initial status test
        from fastapi.testclient import TestClient
        test_client = TestClient(server.app)
        
        with test_client.stream("GET", "/events?test_mode=initial_only") as response:
            assert response.status_code == 200
            
            # Read all content from the stream (should be just the initial event)
            content = response.read().decode('utf-8')
            
            # Parse the SSE event
            lines = content.strip().split('\n')
            data_line = next((line for line in lines if line.startswith("data: ")), None)
            assert data_line is not None
            
            event = json.loads(data_line[6:])  # Remove "data: " prefix
        
        assert event["type"] == "queue_status"
        assert "timestamp" in event
        
        # Verify item serialization
        todo_items = event["data"]["todo"]
        assert len(todo_items) == 1
        
        item_data = todo_items[0]
        assert item_data["id"] == "test-item"
        assert item_data["url"] == "https://youtu.be/test123"
        assert item_data["status"] == "todo"
        assert item_data["title"] == "Test Video Title"
        assert item_data["thumbnail_url"] == "https://img.youtube.com/vi/test123/maxresdefault.jpg"
        assert item_data["channel"] == "Test Channel"
        assert item_data["custom_prompt"] == "Custom test prompt"
        assert "created_at" in item_data
        assert item_data["started_at"] is None
        assert item_data["completed_at"] is None
    
    def test_sse_multiple_status_changes(self, server, mock_queue_manager):
        """Test multiple rapid status changes are properly broadcast."""
        from src.youtube_notion.web.models import QueueStatus
        import asyncio
        
        # Get the registered listener
        assert len(mock_queue_manager.add_status_listener_calls) == 1
        listener = mock_queue_manager.add_status_listener_calls[0]
        
        # Create multiple mock items
        items = []
        for i in range(3):
            item = mock_queue_manager.add_mock_item(
                f"test-item-{i}", 
                f"https://youtu.be/test{i}", 
                QueueStatus.TODO
            )
            items.append(item)
        
        # Create a mock connection queue to track events
        event_queue = asyncio.Queue()
        server._sse_connections.append(event_queue)
        
        # Call the listener for each item (simulating multiple status changes)
        for i, item in enumerate(items):
            listener(f"test-item-{i}", item)
        
        # Verify that events were queued (one for each status change)
        assert event_queue.qsize() == 3
        
        # Verify the events are properly formatted
        for i in range(3):
            event = event_queue.get_nowait()
            assert event["type"] == "status_change"
            assert event["data"]["item_id"] == f"test-item-{i}"
            assert event["data"]["item"]["url"] == f"https://youtu.be/test{i}"
    
class TestSSEIntegration:
    """Integration tests for SSE with queue manager interactions."""
    
    @pytest.fixture
    def mock_queue_manager(self):
        """Create a mock queue manager for integration testing."""
        from tests.fixtures.mock_implementations import MockQueueManager
        return MockQueueManager()
    
    @pytest.fixture
    def server(self, mock_queue_manager):
        """Create a web server instance for integration testing."""
        config = WebServerConfig(debug=True, sse_heartbeat_interval=2)
        return WebServer(mock_queue_manager, config)
    
    def test_sse_listener_registration(self, server, mock_queue_manager):
        """Test that SSE properly registers as a queue status listener."""
        # Server should have registered a status listener
        assert len(mock_queue_manager.add_status_listener_calls) == 1
        
        # The listener should be callable
        listener = mock_queue_manager.add_status_listener_calls[0]
        assert callable(listener)
    
    def test_sse_broadcast_functionality(self, server, mock_queue_manager):
        """Test SSE broadcast method without streaming."""
        from src.youtube_notion.web.models import QueueItem, QueueStatus
        from datetime import datetime
        
        # Create a test queue item
        test_item = QueueItem(
            id="test-123",
            url="https://youtu.be/test",
            status=QueueStatus.TODO,
            created_at=datetime.now()
        )
        
        # Test the broadcast method directly
        event_data = {
            "type": "status_change",
            "data": {
                "item_id": "test-123",
                "item": server._queue_item_to_dict(test_item)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # This should not raise an exception
        server._broadcast_sse_event(event_data)
        
        # Verify the event data structure
        assert event_data["type"] == "status_change"
        assert event_data["data"]["item_id"] == "test-123"
        assert event_data["data"]["item"]["url"] == "https://youtu.be/test"
    
    def test_queue_item_to_dict_conversion(self, server):
        """Test conversion of QueueItem to dictionary."""
        from src.youtube_notion.web.models import QueueItem, QueueStatus
        from datetime import datetime
        
        # Create a test queue item
        test_item = QueueItem(
            id="test-456",
            url="https://youtu.be/test456",
            status=QueueStatus.IN_PROGRESS,
            created_at=datetime.now(),
            title="Test Video",
            channel="Test Channel"
        )
        
        # Convert to dict
        item_dict = server._queue_item_to_dict(test_item)
        
        # Verify all expected fields are present
        assert item_dict["id"] == "test-456"
        assert item_dict["url"] == "https://youtu.be/test456"
        assert item_dict["status"] == "in_progress"
        assert item_dict["title"] == "Test Video"
        assert item_dict["channel"] == "Test Channel"
        assert "created_at" in item_dict
        assert "started_at" in item_dict
        assert "completed_at" in item_dict
    
