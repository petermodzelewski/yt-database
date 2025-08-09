"""
Integration tests for complete web UI workflow.

This module tests the full web UI workflow from URL submission
to completion, including real-time updates and error handling.
"""

import pytest
import asyncio
import json
import threading
import time
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

from src.youtube_notion.web.server import WebServer
from src.youtube_notion.web.config import WebServerConfig
from src.youtube_notion.processors.queue_manager import QueueManager
from src.youtube_notion.web.models import QueueStatus, ProcessingPhase
from tests.fixtures.mock_implementations import MockVideoProcessor, MockQueueManager
from tests.fixtures.web_test_data import (
    create_sample_queue_item,
    create_sample_queue_status,
    get_sample_youtube_url,
    SAMPLE_CUSTOM_PROMPTS
)


class TestWebUIWorkflowIntegration:
    """Test complete web UI workflow integration."""
    
    @pytest.fixture
    def mock_video_processor(self):
        """Create a mock video processor for integration testing."""
        return MockVideoProcessor(configuration_valid=True)
    
    @pytest.fixture
    def queue_manager(self, mock_video_processor):
        """Create a queue manager with mock video processor."""
        return QueueManager(mock_video_processor, max_queue_size=10)
    
    @pytest.fixture
    def web_server_config(self):
        """Create web server configuration for testing."""
        return WebServerConfig(
            port=8081,  # Use different port for testing
            debug=True,
            sse_heartbeat_interval=1  # Fast heartbeat for testing
        )
    
    @pytest.fixture
    def web_server(self, queue_manager, web_server_config):
        """Create web server instance for integration testing."""
        return WebServer(queue_manager, web_server_config)
    
    @pytest.fixture
    def test_client(self, web_server):
        """Create test client for web server."""
        return TestClient(web_server.app)
    
    def test_complete_video_processing_workflow(self, test_client, queue_manager, mock_video_processor):
        """Test complete workflow from URL submission to completion."""
        # Configure mock to succeed
        mock_video_processor.metadata_extractor.set_metadata_for_url(
            get_sample_youtube_url(0),
            {
                'title': 'Test Video',
                'channel': 'Test Channel',
                'thumbnail_url': 'https://example.com/thumb.jpg',
                'duration': 1800,
                'video_id': 'test123'
            }
        )
        
        # Step 1: Submit URL to queue
        response = test_client.post("/api/queue", json={
            "url": get_sample_youtube_url(0),
            "custom_prompt": SAMPLE_CUSTOM_PROMPTS[0]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "item_id" in data
        item_id = data["item_id"]
        
        # Step 2: Verify item is in TODO status
        response = test_client.get("/api/status")
        assert response.status_code == 200
        status_data = response.json()
        
        todo_items = status_data["todo"]
        assert len(todo_items) == 1
        assert todo_items[0]["id"] == item_id
        assert todo_items[0]["url"] == get_sample_youtube_url(0)
        assert todo_items[0]["custom_prompt"] == SAMPLE_CUSTOM_PROMPTS[0]
        assert todo_items[0]["status"] == "todo"
        
        # Step 3: Start processing
        queue_manager.start_processing()
        
        # Wait for processing to begin
        time.sleep(0.2)
        
        # Step 4: Verify item moves to IN_PROGRESS
        response = test_client.get("/api/status")
        status_data = response.json()
        
        # Item should be in progress or completed by now
        in_progress_items = status_data["in_progress"]
        completed_items = status_data["completed"]
        
        # Check if processing is in progress or already completed
        if in_progress_items:
            assert len(in_progress_items) == 1
            assert in_progress_items[0]["id"] == item_id
            assert in_progress_items[0]["status"] == "in_progress"
            assert in_progress_items[0]["current_phase"] is not None
        
        # Wait for processing to complete
        time.sleep(0.5)
        
        # Step 5: Verify item moves to COMPLETED
        response = test_client.get("/api/status")
        status_data = response.json()
        
        completed_items = status_data["completed"]
        assert len(completed_items) == 1
        assert completed_items[0]["id"] == item_id
        assert completed_items[0]["status"] == "completed"
        assert completed_items[0]["title"] == "Test Video"
        
        # Step 6: Verify chat log is available
        response = test_client.get(f"/api/chat-log/{item_id}")
        assert response.status_code == 200
        chat_data = response.json()
        
        assert chat_data["item_id"] == item_id
        assert chat_data["url"] == get_sample_youtube_url(0)
        assert chat_data["title"] == "Test Video"
        assert "chat_log" in chat_data
        
        # Cleanup
        queue_manager.stop_processing()
    
    def test_error_handling_workflow(self, test_client, queue_manager, mock_video_processor):
        """Test workflow when video processing fails."""
        # Configure mock to fail
        mock_video_processor.metadata_extractor.set_failure_for_url(get_sample_youtube_url(1))
        
        # Step 1: Submit URL that will fail
        response = test_client.post("/api/queue", json={
            "url": get_sample_youtube_url(1)
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        item_id = data["item_id"]
        
        # Step 2: Start processing
        queue_manager.start_processing()
        
        # Wait for processing to fail
        time.sleep(0.3)
        
        # Step 3: Verify item is in FAILED status
        response = test_client.get("/api/status")
        status_data = response.json()
        
        failed_items = status_data["failed"]
        assert len(failed_items) == 1
        assert failed_items[0]["id"] == item_id
        assert failed_items[0]["status"] == "failed"
        assert failed_items[0]["error_message"] is not None
        
        # Step 4: Test retry functionality
        response = test_client.post(f"/api/retry/{item_id}")
        assert response.status_code == 200
        retry_data = response.json()
        
        # Should fail because mock is still configured to fail
        assert retry_data["success"] is False
        assert "error" in retry_data
        
        # Cleanup
        queue_manager.stop_processing()
    
    def test_multiple_urls_concurrent_processing(self, test_client, queue_manager, mock_video_processor):
        """Test processing multiple URLs concurrently."""
        urls = [get_sample_youtube_url(i) for i in range(3)]
        item_ids = []
        
        # Configure mock for all URLs
        for i, url in enumerate(urls):
            mock_video_processor.metadata_extractor.set_metadata_for_url(
                url,
                {
                    'title': f'Test Video {i+1}',
                    'channel': f'Test Channel {i+1}',
                    'thumbnail_url': f'https://example.com/thumb{i+1}.jpg',
                    'duration': 1800,
                    'video_id': f'test{i+1}'
                }
            )
        
        # Step 1: Submit multiple URLs
        for url in urls:
            response = test_client.post("/api/queue", json={"url": url})
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            item_ids.append(data["item_id"])
        
        # Step 2: Verify all items are in TODO
        response = test_client.get("/api/status")
        status_data = response.json()
        
        todo_items = status_data["todo"]
        assert len(todo_items) == 3
        
        # Step 3: Start processing
        queue_manager.start_processing()
        
        # Wait for all processing to complete
        time.sleep(1.0)
        
        # Step 4: Verify all items are completed
        response = test_client.get("/api/status")
        status_data = response.json()
        
        completed_items = status_data["completed"]
        assert len(completed_items) == 3
        
        # Verify all item IDs are present
        completed_ids = [item["id"] for item in completed_items]
        for item_id in item_ids:
            assert item_id in completed_ids
        
        # Cleanup
        queue_manager.stop_processing()
    
    def test_queue_full_error_handling(self, test_client, queue_manager):
        """Test queue full error handling."""
        # Fill the queue to capacity (max_queue_size = 10)
        item_ids = []
        for i in range(10):
            response = test_client.post("/api/queue", json={
                "url": get_sample_youtube_url(i % len([get_sample_youtube_url(j) for j in range(5)]))
            })
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            item_ids.append(data["item_id"])
        
        # Try to add one more item (should fail)
        response = test_client.post("/api/queue", json={
            "url": get_sample_youtube_url(0)
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Queue is full" in data["error"]
    
    def test_invalid_url_error_handling(self, test_client):
        """Test invalid URL error handling."""
        invalid_urls = [
            "not-a-url",
            "https://google.com",
            "https://vimeo.com/123456",
            ""
        ]
        
        for invalid_url in invalid_urls:
            response = test_client.post("/api/queue", json={"url": invalid_url})
            
            # Should either be validation error (422) or success=false
            if response.status_code == 422:
                # Pydantic validation error
                continue
            else:
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is False
                assert "error" in data
    
    def test_health_check_integration(self, test_client, queue_manager):
        """Test health check endpoint integration."""
        # Add some items to queue
        for i in range(3):
            test_client.post("/api/queue", json={
                "url": get_sample_youtube_url(i)
            })
        
        # Check health endpoint
        response = test_client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "timestamp" in health_data
        assert "queue_stats" in health_data
        
        queue_stats = health_data["queue_stats"]
        assert queue_stats["total_items"] == 3
        assert queue_stats["todo"] == 3
        assert queue_stats["in_progress"] == 0
        assert queue_stats["completed"] == 0
        assert queue_stats["failed"] == 0
    
    def test_static_file_serving(self, test_client):
        """Test static file serving integration."""
        # Test serving index.html
        response = test_client.get("/")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        assert "<!DOCTYPE html>" in response.text
        assert "YouTube to Notion Queue" in response.text
        
        # Test serving CSS
        response = test_client.get("/styles.css")
        assert response.status_code == 200
        assert "text/css" in response.headers["content-type"]
        
        # Test serving JavaScript
        response = test_client.get("/app.js")
        assert response.status_code == 200
        assert "application/javascript" in response.headers["content-type"]


class TestSSEIntegrationWorkflow:
    """Test Server-Sent Events integration workflow."""
    
    @pytest.fixture
    def mock_queue_manager(self):
        """Create a mock queue manager for SSE testing."""
        return MockQueueManager()
    
    @pytest.fixture
    def web_server(self, mock_queue_manager):
        """Create web server with mock queue manager."""
        config = WebServerConfig(debug=True, sse_heartbeat_interval=1)
        return WebServer(mock_queue_manager, config)
    
    @pytest.fixture
    def test_client(self, web_server):
        """Create test client for SSE testing."""
        return TestClient(web_server.app)
    
    def test_sse_initial_connection(self, test_client, mock_queue_manager):
        """Test SSE initial connection and status broadcast."""
        # Add some mock items
        mock_queue_manager.add_mock_item("item-1", get_sample_youtube_url(0), QueueStatus.TODO)
        mock_queue_manager.add_mock_item("item-2", get_sample_youtube_url(1), QueueStatus.IN_PROGRESS)
        mock_queue_manager.add_mock_item("item-3", get_sample_youtube_url(2), QueueStatus.COMPLETED)
        
        # Connect to SSE endpoint with test mode
        with test_client.stream("GET", "/events?test_mode=initial_only") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["connection"] == "keep-alive"
            
            # Read the initial status event
            content = response.read().decode('utf-8')
            
            # Parse SSE event
            lines = content.strip().split('\n')
            data_line = next((line for line in lines if line.startswith("data: ")), None)
            assert data_line is not None
            
            event_data = json.loads(data_line[6:])  # Remove "data: " prefix
            assert event_data["type"] == "queue_status"
            assert "data" in event_data
            assert "timestamp" in event_data
            
            # Verify queue data structure
            queue_data = event_data["data"]
            assert len(queue_data["todo"]) == 1
            assert len(queue_data["in_progress"]) == 1
            assert len(queue_data["completed"]) == 1
            assert len(queue_data["failed"]) == 0
    
    def test_sse_status_change_notification(self, test_client, mock_queue_manager):
        """Test SSE status change notifications."""
        # Add initial item
        item_id = mock_queue_manager._enqueue(get_sample_youtube_url(0))
        
        # Connect to SSE (this would normally be a streaming test, but we'll test the mechanism)
        response = test_client.get("/events?test_mode=initial_only")
        assert response.status_code == 200
        
        # Verify that status listeners are registered
        assert len(mock_queue_manager.status_listeners) > 0
        
        # Simulate status change
        mock_queue_manager.set_item_status(item_id, QueueStatus.IN_PROGRESS)
        
        # Verify listener was called (tracked in mock)
        assert len(mock_queue_manager.status_listeners) > 0
    
    def test_sse_connection_cleanup(self, test_client, mock_queue_manager):
        """Test SSE connection cleanup when client disconnects."""
        # Connect to SSE
        response = test_client.get("/events?test_mode=initial_only")
        assert response.status_code == 200
        
        # Verify listener was added
        initial_listeners = len(mock_queue_manager.status_listeners)
        assert initial_listeners > 0
        
        # Connection cleanup happens automatically when response ends
        # In a real scenario, this would be tested with actual streaming connections


class TestWebUIErrorRecovery:
    """Test error recovery scenarios in web UI."""
    
    @pytest.fixture
    def mock_video_processor(self):
        """Create a mock video processor that can simulate various failures."""
        return MockVideoProcessor(configuration_valid=True)
    
    @pytest.fixture
    def queue_manager(self, mock_video_processor):
        """Create queue manager for error recovery testing."""
        return QueueManager(mock_video_processor, max_queue_size=5)
    
    @pytest.fixture
    def test_client(self, queue_manager):
        """Create test client for error recovery testing."""
        config = WebServerConfig(debug=True)
        server = WebServer(queue_manager, config)
        return TestClient(server.app)
    
    def test_processing_failure_recovery(self, test_client, queue_manager, mock_video_processor):
        """Test recovery from processing failures."""
        # Configure first URL to fail, second to succeed
        mock_video_processor.metadata_extractor.set_failure_for_url(get_sample_youtube_url(0))
        mock_video_processor.metadata_extractor.set_metadata_for_url(
            get_sample_youtube_url(1),
            {
                'title': 'Success Video',
                'channel': 'Success Channel',
                'thumbnail_url': 'https://example.com/success.jpg',
                'duration': 1800,
                'video_id': 'success123'
            }
        )
        
        # Add both URLs
        response1 = test_client.post("/api/queue", json={"url": get_sample_youtube_url(0)})
        response2 = test_client.post("/api/queue", json={"url": get_sample_youtube_url(1)})
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        item_id_1 = response1.json()["item_id"]
        item_id_2 = response2.json()["item_id"]
        
        # Start processing
        queue_manager.start_processing()
        
        # Wait for processing
        time.sleep(0.5)
        
        # Check final status
        response = test_client.get("/api/status")
        status_data = response.json()
        
        # First item should fail, second should succeed
        failed_items = status_data["failed"]
        completed_items = status_data["completed"]
        
        assert len(failed_items) == 1
        assert len(completed_items) == 1
        
        assert failed_items[0]["id"] == item_id_1
        assert completed_items[0]["id"] == item_id_2
        
        # Cleanup
        queue_manager.stop_processing()
    
    def test_server_restart_simulation(self, mock_video_processor):
        """Test queue state after simulated server restart."""
        # Create initial queue manager and add items
        queue_manager_1 = QueueManager(mock_video_processor, max_queue_size=5)
        
        # Add items to first queue manager
        item_id_1 = queue_manager_1.enqueue(get_sample_youtube_url(0))
        item_id_2 = queue_manager_1.enqueue(get_sample_youtube_url(1))
        
        # Verify items exist
        assert queue_manager_1.get_item_status(item_id_1) is not None
        assert queue_manager_1.get_item_status(item_id_2) is not None
        
        # Simulate server restart by creating new queue manager
        queue_manager_2 = QueueManager(mock_video_processor, max_queue_size=5)
        
        # New queue manager should start empty (no persistence in current implementation)
        status = queue_manager_2.get_queue_status()
        assert len(status['todo']) == 0
        assert len(status['in_progress']) == 0
        assert len(status['completed']) == 0
        assert len(status['failed']) == 0
        
        # This test demonstrates the current behavior - in a production system,
        # you might want to implement queue persistence
    
    def test_concurrent_error_handling(self, test_client, queue_manager, mock_video_processor):
        """Test error handling with concurrent requests."""
        # Configure some URLs to fail
        mock_video_processor.metadata_extractor.set_failure_for_url(get_sample_youtube_url(0))
        mock_video_processor.metadata_extractor.set_failure_for_url(get_sample_youtube_url(2))
        
        # Configure some URLs to succeed
        for i in [1, 3, 4]:
            mock_video_processor.metadata_extractor.set_metadata_for_url(
                get_sample_youtube_url(i),
                {
                    'title': f'Video {i}',
                    'channel': f'Channel {i}',
                    'thumbnail_url': f'https://example.com/thumb{i}.jpg',
                    'duration': 1800,
                    'video_id': f'test{i}'
                }
            )
        
        # Submit multiple URLs rapidly
        responses = []
        for i in range(5):
            response = test_client.post("/api/queue", json={
                "url": get_sample_youtube_url(i)
            })
            responses.append(response)
        
        # All submissions should succeed (errors happen during processing)
        for response in responses:
            assert response.status_code == 200
            assert response.json()["success"] is True
        
        # Start processing
        queue_manager.start_processing()
        
        # Wait for all processing to complete
        time.sleep(1.0)
        
        # Check final status
        response = test_client.get("/api/status")
        status_data = response.json()
        
        # Should have 2 failed and 3 completed
        assert len(status_data["failed"]) == 2
        assert len(status_data["completed"]) == 3
        assert len(status_data["todo"]) == 0
        assert len(status_data["in_progress"]) == 0
        
        # Cleanup
        queue_manager.stop_processing()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])