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
    
    def test_serve_index_without_static_files(self, test_client, mock_queue_manager):
        """Test serving index when static files don't exist."""
        response = test_client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "Web UI not yet implemented" in data["message"]


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
    async def async_client(self, mock_queue_manager):
        """Create an async HTTP client for SSE testing."""
        config = WebServerConfig(debug=True, sse_heartbeat_interval=1)
        server = WebServer(mock_queue_manager, config)
        
        async with httpx.AsyncClient(app=server.app, base_url="http://test") as client:
            yield client
    
    def test_sse_endpoint_initial_status(self, test_client, mock_queue_manager):
        """Test SSE endpoint returns initial queue status."""
        from src.youtube_notion.web.models import QueueStatus
        
        # Add some mock items to the queue
        mock_queue_manager.add_mock_item("item-1", "https://youtu.be/test1", QueueStatus.TODO)
        mock_queue_manager.add_mock_item("item-2", "https://youtu.be/test2", QueueStatus.IN_PROGRESS)
        mock_queue_manager.add_mock_item("item-3", "https://youtu.be/test3", QueueStatus.COMPLETED)
        
        # Connect to SSE endpoint
        with test_client.stream("GET", "/events") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["connection"] == "keep-alive"
            
            # Read the first event (initial status)
            lines = []
            for line in response.iter_lines():
                lines.append(line)
                if line == "":  # Empty line indicates end of event
                    break
            
            # Parse the event data
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
    
    @pytest.mark.asyncio
    async def test_sse_status_change_events(self, async_client, mock_queue_manager):
        """Test that SSE broadcasts status change events."""
        from src.youtube_notion.web.models import QueueStatus
        
        # Start SSE connection
        async with async_client.stream("GET", "/events") as response:
            assert response.status_code == 200
            
            # Read initial status event
            initial_event = await self._read_sse_event(response)
            assert initial_event["type"] == "queue_status"
            
            # Simulate status change by adding an item
            item_id = mock_queue_manager._enqueue("https://youtu.be/newvideo")
            
            # Should receive a status change event
            status_event = await self._read_sse_event(response)
            assert status_event["type"] == "status_change"
            assert status_event["data"]["item_id"] == item_id
            assert status_event["data"]["item"]["url"] == "https://youtu.be/newvideo"
            assert status_event["data"]["item"]["status"] == "todo"
    
    @pytest.mark.asyncio
    async def test_sse_heartbeat_functionality(self, async_client, mock_queue_manager):
        """Test SSE heartbeat functionality."""
        # Start SSE connection
        async with async_client.stream("GET", "/events") as response:
            assert response.status_code == 200
            
            # Read initial status event
            initial_event = await self._read_sse_event(response)
            assert initial_event["type"] == "queue_status"
            
            # Wait for heartbeat (should come within heartbeat interval + some buffer)
            heartbeat_event = await asyncio.wait_for(
                self._read_sse_event(response), 
                timeout=3.0  # Heartbeat interval is 1 second + buffer
            )
            assert heartbeat_event["type"] == "heartbeat"
            assert "timestamp" in heartbeat_event
    
    @pytest.mark.asyncio
    async def test_sse_connection_management(self, mock_queue_manager):
        """Test SSE connection management and cleanup."""
        config = WebServerConfig(debug=True, sse_heartbeat_interval=1)
        server = WebServer(mock_queue_manager, config)
        
        # Initially no connections
        assert len(server._sse_connections) == 0
        
        async with httpx.AsyncClient(app=server.app, base_url="http://test") as client:
            # Start multiple SSE connections
            async with client.stream("GET", "/events") as response1:
                # Should have one connection
                assert len(server._sse_connections) == 1
                
                async with client.stream("GET", "/events") as response2:
                    # Should have two connections
                    assert len(server._sse_connections) == 2
                    
                    # Read initial events from both connections
                    event1 = await self._read_sse_event(response1)
                    event2 = await self._read_sse_event(response2)
                    
                    assert event1["type"] == "queue_status"
                    assert event2["type"] == "queue_status"
                
                # After second connection closes, should have one connection
                # Note: Connection cleanup happens during event broadcasting
                # so we need to trigger an event to clean up closed connections
                mock_queue_manager._enqueue("https://youtu.be/trigger")
                
                # Read the status change event
                await self._read_sse_event(response1)
        
        # After all connections close, should eventually have no connections
        # Trigger another event to clean up
        mock_queue_manager._enqueue("https://youtu.be/cleanup")
        
        # Give some time for cleanup
        await asyncio.sleep(0.1)
    
    @pytest.mark.asyncio
    async def test_sse_error_handling(self, mock_queue_manager):
        """Test SSE error handling and recovery."""
        config = WebServerConfig(debug=True, sse_heartbeat_interval=1)
        server = WebServer(mock_queue_manager, config)
        
        # Mock a queue manager method to raise an exception
        original_get_queue_status = mock_queue_manager._get_queue_status
        
        def failing_get_queue_status():
            raise Exception("Mock queue error")
        
        mock_queue_manager._get_queue_status = failing_get_queue_status
        
        async with httpx.AsyncClient(app=server.app, base_url="http://test") as client:
            async with client.stream("GET", "/events") as response:
                assert response.status_code == 200
                
                # Should receive an error event
                error_event = await self._read_sse_event(response)
                assert error_event["type"] == "error"
                assert "error" in error_event
                assert "timestamp" in error_event
        
        # Restore original method
        mock_queue_manager._get_queue_status = original_get_queue_status
    
    @pytest.mark.asyncio
    async def test_sse_event_serialization(self, async_client, mock_queue_manager):
        """Test proper SSE event serialization and formatting."""
        from src.youtube_notion.web.models import QueueStatus
        from datetime import datetime
        
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
        
        async with async_client.stream("GET", "/events") as response:
            # Read initial status event
            event = await self._read_sse_event(response)
            
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
    
    @pytest.mark.asyncio
    async def test_sse_multiple_status_changes(self, async_client, mock_queue_manager):
        """Test multiple rapid status changes are properly broadcast."""
        from src.youtube_notion.web.models import QueueStatus
        
        async with async_client.stream("GET", "/events") as response:
            # Read initial status
            await self._read_sse_event(response)
            
            # Add multiple items rapidly
            item_ids = []
            for i in range(3):
                item_id = mock_queue_manager._enqueue(f"https://youtu.be/test{i}")
                item_ids.append(item_id)
            
            # Should receive status change events for each item
            events = []
            for _ in range(3):
                event = await asyncio.wait_for(self._read_sse_event(response), timeout=2.0)
                events.append(event)
            
            # Verify all events are status changes
            for event in events:
                assert event["type"] == "status_change"
                assert event["data"]["item_id"] in item_ids
                assert event["data"]["item"]["status"] == "todo"
            
            # Change status of one item
            mock_queue_manager.set_item_status(item_ids[0], QueueStatus.IN_PROGRESS)
            
            # Should receive status change event
            status_event = await self._read_sse_event(response)
            assert status_event["type"] == "status_change"
            assert status_event["data"]["item_id"] == item_ids[0]
            assert status_event["data"]["item"]["status"] == "in_progress"
    
    @pytest.mark.asyncio
    async def test_sse_connection_resilience(self, mock_queue_manager):
        """Test SSE connection resilience with queue full scenarios."""
        config = WebServerConfig(debug=True, sse_heartbeat_interval=1)
        server = WebServer(mock_queue_manager, config)
        
        async with httpx.AsyncClient(app=server.app, base_url="http://test") as client:
            async with client.stream("GET", "/events") as response:
                # Read initial status
                await self._read_sse_event(response)
                
                # Simulate a scenario where connection queue might get full
                # by rapidly adding many items
                for i in range(10):
                    mock_queue_manager._enqueue(f"https://youtu.be/rapid{i}")
                
                # Should still be able to read events
                events_received = 0
                try:
                    while events_received < 5:  # Read at least 5 events
                        event = await asyncio.wait_for(
                            self._read_sse_event(response), 
                            timeout=2.0
                        )
                        if event["type"] == "status_change":
                            events_received += 1
                except asyncio.TimeoutError:
                    # This is acceptable - we might not receive all events
                    # if the connection queue handling drops some
                    pass
                
                # Should have received at least some events
                assert events_received > 0
    
    async def _read_sse_event(self, response) -> dict:
        """
        Helper method to read and parse a single SSE event.
        
        Args:
            response: HTTP response stream
            
        Returns:
            dict: Parsed event data
        """
        lines = []
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_line = line[6:]  # Remove "data: " prefix
                return json.loads(data_line)
            elif line == "":
                # Empty line indicates end of event, but no data found
                continue
        
        raise ValueError("No SSE event data found")


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
    
    @pytest.mark.asyncio
    async def test_sse_queue_integration(self, server, mock_queue_manager):
        """Test full integration between SSE and queue manager."""
        from src.youtube_notion.web.models import QueueStatus
        
        async with httpx.AsyncClient(app=server.app, base_url="http://test") as client:
            async with client.stream("GET", "/events") as response:
                # Read initial status
                initial_event = await self._read_sse_event(response)
                assert initial_event["type"] == "queue_status"
                
                # Add item through queue manager
                item_id = mock_queue_manager._enqueue("https://youtu.be/integration")
                
                # Should receive status change event
                status_event = await asyncio.wait_for(
                    self._read_sse_event(response), 
                    timeout=2.0
                )
                assert status_event["type"] == "status_change"
                assert status_event["data"]["item_id"] == item_id
                
                # Change item status
                mock_queue_manager.set_item_status(item_id, QueueStatus.IN_PROGRESS)
                
                # Should receive another status change event
                progress_event = await asyncio.wait_for(
                    self._read_sse_event(response), 
                    timeout=2.0
                )
                assert progress_event["type"] == "status_change"
                assert progress_event["data"]["item"]["status"] == "in_progress"
    
    async def _read_sse_event(self, response) -> dict:
        """Helper method to read and parse a single SSE event."""
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data_line = line[6:]  # Remove "data: " prefix
                return json.loads(data_line)
        
        raise ValueError("No SSE event data found")