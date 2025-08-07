"""
Unit tests for the FastAPI web server.

This module tests the WebServer class and its API endpoints using FastAPI's
TestClient for isolated testing without external dependencies.
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

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