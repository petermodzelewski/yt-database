"""
Unit tests for QueueManager component.

This module contains comprehensive tests for the QueueManager class,
including thread-safe operations, concurrency handling, observable
pattern, and error scenarios.
"""

import pytest
import threading
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.youtube_notion.processors.queue_manager import QueueManager
from src.youtube_notion.web.models import QueueItem, QueueStatus, ProcessingPhase
from src.youtube_notion.utils.exceptions import VideoProcessingError, ConfigurationError


class TestQueueManagerInitialization:
    """Test QueueManager initialization and configuration."""
    
    def test_init_with_valid_processor(self):
        """Test successful initialization with valid VideoProcessor."""
        mock_processor = Mock()
        queue_manager = QueueManager(mock_processor)
        
        assert queue_manager.video_processor == mock_processor
        assert queue_manager.max_queue_size == 100  # default
        assert not queue_manager._processing_active
        assert len(queue_manager._items) == 0
        assert len(queue_manager._status_listeners) == 0
    
    def test_init_with_custom_max_size(self):
        """Test initialization with custom max queue size."""
        mock_processor = Mock()
        queue_manager = QueueManager(mock_processor, max_queue_size=50)
        
        assert queue_manager.max_queue_size == 50
    
    def test_init_with_none_processor_raises_error(self):
        """Test that initialization with None processor raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="VideoProcessor is required"):
            QueueManager(None)
    
    def test_init_with_invalid_processor_raises_error(self):
        """Test that initialization with invalid processor raises ConfigurationError."""
        with pytest.raises(ConfigurationError, match="VideoProcessor is required"):
            QueueManager("not_a_processor")


class TestQueueOperations:
    """Test basic queue operations (enqueue, dequeue, status)."""
    
    @pytest.fixture
    def queue_manager(self):
        """Create a QueueManager instance for testing."""
        mock_processor = Mock()
        return QueueManager(mock_processor, max_queue_size=5)
    
    def test_enqueue_valid_url(self, queue_manager):
        """Test enqueuing a valid URL."""
        url = "https://youtu.be/test123"
        item_id = queue_manager.enqueue(url)
        
        assert isinstance(item_id, str)
        assert len(item_id) > 0
        
        # Check item was added to internal storage
        item = queue_manager.get_item_status(item_id)
        assert item is not None
        assert item.url == url
        assert item.status == QueueStatus.TODO
        assert item.custom_prompt is None
        assert isinstance(item.created_at, datetime)
    
    def test_enqueue_with_custom_prompt(self, queue_manager):
        """Test enqueuing URL with custom prompt."""
        url = "https://youtu.be/test123"
        custom_prompt = "Custom summary prompt"
        item_id = queue_manager.enqueue(url, custom_prompt)
        
        item = queue_manager.get_item_status(item_id)
        assert item.custom_prompt == custom_prompt
    
    def test_enqueue_empty_url_raises_error(self, queue_manager):
        """Test that enqueuing empty URL raises ValueError."""
        with pytest.raises(ValueError, match="URL must be a non-empty string"):
            queue_manager.enqueue("")
    
    def test_enqueue_none_url_raises_error(self, queue_manager):
        """Test that enqueuing None URL raises ValueError."""
        with pytest.raises(ValueError, match="URL must be a non-empty string"):
            queue_manager.enqueue(None)
    
    def test_enqueue_non_string_url_raises_error(self, queue_manager):
        """Test that enqueuing non-string URL raises ValueError."""
        with pytest.raises(ValueError, match="URL must be a non-empty string"):
            queue_manager.enqueue(123)
    
    def test_enqueue_queue_full_raises_error(self, queue_manager):
        """Test that enqueuing when queue is full raises ValueError."""
        # Fill the queue to capacity (max_queue_size = 5)
        for i in range(5):
            queue_manager.enqueue(f"https://youtu.be/test{i}")
        
        # Try to add one more
        with pytest.raises(ValueError, match="Queue is full"):
            queue_manager.enqueue("https://youtu.be/overflow")
    
    def test_dequeue_with_items(self, queue_manager):
        """Test dequeuing when items are available."""
        url = "https://youtu.be/test123"
        item_id = queue_manager.enqueue(url)
        
        dequeued_id = queue_manager.dequeue()
        assert dequeued_id == item_id
    
    def test_dequeue_empty_queue(self, queue_manager):
        """Test dequeuing from empty queue returns None."""
        result = queue_manager.dequeue()
        assert result is None
    
    def test_get_item_status_existing_item(self, queue_manager):
        """Test getting status of existing item."""
        url = "https://youtu.be/test123"
        item_id = queue_manager.enqueue(url)
        
        item = queue_manager.get_item_status(item_id)
        assert item is not None
        assert item.id == item_id
        assert item.url == url
    
    def test_get_item_status_nonexistent_item(self, queue_manager):
        """Test getting status of non-existent item returns None."""
        result = queue_manager.get_item_status("nonexistent-id")
        assert result is None


class TestQueueStatusManagement:
    """Test queue status tracking and updates."""
    
    @pytest.fixture
    def queue_manager(self):
        """Create a QueueManager instance for testing."""
        mock_processor = Mock()
        return QueueManager(mock_processor)
    
    def test_get_queue_status_empty(self, queue_manager):
        """Test getting status of empty queue."""
        status = queue_manager.get_queue_status()
        
        assert isinstance(status, dict)
        assert set(status.keys()) == {'todo', 'in_progress', 'completed', 'failed'}
        assert all(len(items) == 0 for items in status.values())
    
    def test_get_queue_status_with_items(self, queue_manager):
        """Test getting status with various items."""
        # Add items in different states
        id1 = queue_manager.enqueue("https://youtu.be/test1")
        id2 = queue_manager.enqueue("https://youtu.be/test2")
        id3 = queue_manager.enqueue("https://youtu.be/test3")
        
        # Update some items to different statuses
        queue_manager.update_item_status(id2, QueueStatus.IN_PROGRESS)
        queue_manager.update_item_status(id3, QueueStatus.COMPLETED)
        
        status = queue_manager.get_queue_status()
        
        assert len(status['todo']) == 1
        assert len(status['in_progress']) == 1
        assert len(status['completed']) == 1
        assert len(status['failed']) == 0
        
        assert status['todo'][0].id == id1
        assert status['in_progress'][0].id == id2
        assert status['completed'][0].id == id3
    
    def test_update_item_status_valid_item(self, queue_manager):
        """Test updating status of valid item."""
        item_id = queue_manager.enqueue("https://youtu.be/test123")
        
        # Update to in progress
        success = queue_manager.update_item_status(item_id, QueueStatus.IN_PROGRESS)
        assert success is True
        
        item = queue_manager.get_item_status(item_id)
        assert item.status == QueueStatus.IN_PROGRESS
        assert item.started_at is not None
    
    def test_update_item_status_with_error_message(self, queue_manager):
        """Test updating status with error message."""
        item_id = queue_manager.enqueue("https://youtu.be/test123")
        error_msg = "Processing failed"
        
        success = queue_manager.update_item_status(
            item_id, 
            QueueStatus.FAILED, 
            error_message=error_msg
        )
        assert success is True
        
        item = queue_manager.get_item_status(item_id)
        assert item.status == QueueStatus.FAILED
        assert item.error_message == error_msg
        assert item.completed_at is not None
    
    def test_update_item_status_with_processing_info(self, queue_manager):
        """Test updating status with processing phase and chunk info."""
        item_id = queue_manager.enqueue("https://youtu.be/test123")
        
        success = queue_manager.update_item_status(
            item_id,
            QueueStatus.IN_PROGRESS,
            current_phase=ProcessingPhase.CHUNK_PROCESSING.value,
            current_chunk=2,
            total_chunks=4
        )
        assert success is True
        
        item = queue_manager.get_item_status(item_id)
        assert item.current_phase == ProcessingPhase.CHUNK_PROCESSING.value
        assert item.current_chunk == 2
        assert item.total_chunks == 4
    
    def test_update_item_status_nonexistent_item(self, queue_manager):
        """Test updating status of non-existent item returns False."""
        success = queue_manager.update_item_status("nonexistent", QueueStatus.COMPLETED)
        assert success is False


class TestObservablePattern:
    """Test status change listeners and observable pattern."""
    
    @pytest.fixture
    def queue_manager(self):
        """Create a QueueManager instance for testing."""
        mock_processor = Mock()
        return QueueManager(mock_processor)
    
    def test_add_status_listener(self, queue_manager):
        """Test adding status change listener."""
        listener = Mock()
        queue_manager.add_status_listener(listener)
        
        assert listener in queue_manager._status_listeners
    
    def test_add_invalid_listener_raises_error(self, queue_manager):
        """Test adding non-callable listener raises ValueError."""
        with pytest.raises(ValueError, match="Callback must be callable"):
            queue_manager.add_status_listener("not_callable")
    
    def test_remove_status_listener(self, queue_manager):
        """Test removing status change listener."""
        listener = Mock()
        queue_manager.add_status_listener(listener)
        queue_manager.remove_status_listener(listener)
        
        assert listener not in queue_manager._status_listeners
    
    def test_remove_nonexistent_listener(self, queue_manager):
        """Test removing non-existent listener doesn't raise error."""
        listener = Mock()
        # Should not raise an error
        queue_manager.remove_status_listener(listener)
    
    def test_listener_called_on_enqueue(self, queue_manager):
        """Test that listeners are called when item is enqueued."""
        listener = Mock()
        queue_manager.add_status_listener(listener)
        
        item_id = queue_manager.enqueue("https://youtu.be/test123")
        
        listener.assert_called_once()
        call_args = listener.call_args[0]
        assert call_args[0] == item_id
        assert isinstance(call_args[1], QueueItem)
        assert call_args[1].status == QueueStatus.TODO
    
    def test_listener_called_on_status_update(self, queue_manager):
        """Test that listeners are called when status is updated."""
        listener = Mock()
        queue_manager.add_status_listener(listener)
        
        item_id = queue_manager.enqueue("https://youtu.be/test123")
        listener.reset_mock()  # Clear the enqueue call
        
        queue_manager.update_item_status(item_id, QueueStatus.IN_PROGRESS)
        
        listener.assert_called_once()
        call_args = listener.call_args[0]
        assert call_args[0] == item_id
        assert call_args[1].status == QueueStatus.IN_PROGRESS
    
    def test_multiple_listeners_called(self, queue_manager):
        """Test that multiple listeners are all called."""
        listener1 = Mock()
        listener2 = Mock()
        queue_manager.add_status_listener(listener1)
        queue_manager.add_status_listener(listener2)
        
        queue_manager.enqueue("https://youtu.be/test123")
        
        listener1.assert_called_once()
        listener2.assert_called_once()
    
    def test_listener_exception_doesnt_affect_others(self, queue_manager):
        """Test that exception in one listener doesn't affect others."""
        def failing_listener(item_id, item):
            raise Exception("Listener failed")
        
        working_listener = Mock()
        
        queue_manager.add_status_listener(failing_listener)
        queue_manager.add_status_listener(working_listener)
        
        # Should not raise exception
        queue_manager.enqueue("https://youtu.be/test123")
        
        # Working listener should still be called
        working_listener.assert_called_once()


class TestBackgroundProcessing:
    """Test background processing thread functionality."""
    
    @pytest.fixture
    def queue_manager(self):
        """Create a QueueManager instance for testing."""
        mock_processor = Mock()
        mock_processor.process_video.return_value = True
        return QueueManager(mock_processor)
    
    def test_start_processing(self, queue_manager):
        """Test starting background processing."""
        queue_manager.start_processing()
        
        assert queue_manager._processing_active is True
        assert queue_manager._processing_thread is not None
        assert queue_manager._processing_thread.is_alive()
        
        # Clean up
        queue_manager.stop_processing()
    
    def test_start_processing_already_active_raises_error(self, queue_manager):
        """Test starting processing when already active raises RuntimeError."""
        queue_manager.start_processing()
        
        with pytest.raises(RuntimeError, match="Processing is already active"):
            queue_manager.start_processing()
        
        # Clean up
        queue_manager.stop_processing()
    
    def test_stop_processing(self, queue_manager):
        """Test stopping background processing."""
        queue_manager.start_processing()
        
        success = queue_manager.stop_processing()
        
        assert success is True
        assert queue_manager._processing_active is False
        assert queue_manager._processing_thread is None or not queue_manager._processing_thread.is_alive()
    
    def test_stop_processing_not_active(self, queue_manager):
        """Test stopping processing when not active returns True."""
        success = queue_manager.stop_processing()
        assert success is True
    
    def test_context_manager(self, queue_manager):
        """Test using QueueManager as context manager."""
        with queue_manager as qm:
            assert qm._processing_active is True
        
        assert queue_manager._processing_active is False
    
    def test_background_processing_processes_items(self, queue_manager):
        """Test that background thread processes enqueued items."""
        # Set up mock to track calls
        queue_manager.video_processor.process_video.return_value = True
        
        # Start processing
        queue_manager.start_processing()
        
        # Add item to queue
        item_id = queue_manager.enqueue("https://youtu.be/test123")
        
        # Wait for processing
        time.sleep(0.2)
        
        # Check that item was processed
        item = queue_manager.get_item_status(item_id)
        assert item.status == QueueStatus.COMPLETED
        
        # Check that video processor was called
        queue_manager.video_processor.process_video.assert_called_once_with(
            "https://youtu.be/test123", None
        )
        
        # Clean up
        queue_manager.stop_processing()
    
    def test_background_processing_handles_failures(self, queue_manager):
        """Test that background thread handles processing failures."""
        # Set up mock to return failure
        queue_manager.video_processor.process_video.return_value = False
        
        # Start processing
        queue_manager.start_processing()
        
        # Add item to queue
        item_id = queue_manager.enqueue("https://youtu.be/test123")
        
        # Wait for processing
        time.sleep(0.2)
        
        # Check that item failed
        item = queue_manager.get_item_status(item_id)
        assert item.status == QueueStatus.FAILED
        assert item.error_message == "Video processing failed"
        
        # Clean up
        queue_manager.stop_processing()
    
    def test_background_processing_handles_exceptions(self, queue_manager):
        """Test that background thread handles processing exceptions."""
        # Set up mock to raise exception
        queue_manager.video_processor.process_video.side_effect = Exception("Processing error")
        
        # Start processing
        queue_manager.start_processing()
        
        # Add item to queue
        item_id = queue_manager.enqueue("https://youtu.be/test123")
        
        # Wait for processing
        time.sleep(0.2)
        
        # Check that item failed with error message
        item = queue_manager.get_item_status(item_id)
        assert item.status == QueueStatus.FAILED
        assert "Processing error" in item.error_message
        
        # Clean up
        queue_manager.stop_processing()


class TestConcurrency:
    """Test thread-safe operations and concurrency handling."""
    
    @pytest.fixture
    def queue_manager(self):
        """Create a QueueManager instance for testing."""
        mock_processor = Mock()
        mock_processor.process_video.return_value = True
        return QueueManager(mock_processor, max_queue_size=100)
    
    def test_concurrent_enqueue_operations(self, queue_manager):
        """Test multiple threads enqueuing items concurrently."""
        results = []
        errors = []
        
        def enqueue_items(thread_id, count):
            try:
                for i in range(count):
                    item_id = queue_manager.enqueue(f"https://youtu.be/thread{thread_id}_item{i}")
                    results.append(item_id)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=enqueue_items, args=(i, 10))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 50  # 5 threads * 10 items each
        assert len(set(results)) == 50  # All IDs should be unique
        
        # Check that all items are in the queue
        status = queue_manager.get_queue_status()
        assert len(status['todo']) == 50
    
    def test_concurrent_status_updates(self, queue_manager):
        """Test multiple threads updating item status concurrently."""
        # Add items to queue
        item_ids = []
        for i in range(10):
            item_id = queue_manager.enqueue(f"https://youtu.be/test{i}")
            item_ids.append(item_id)
        
        results = []
        errors = []
        
        def update_status(item_id, status):
            try:
                success = queue_manager.update_item_status(item_id, status)
                results.append((item_id, success))
            except Exception as e:
                errors.append(e)
        
        # Create threads to update different items
        threads = []
        for i, item_id in enumerate(item_ids):
            status = QueueStatus.IN_PROGRESS if i % 2 == 0 else QueueStatus.COMPLETED
            thread = threading.Thread(target=update_status, args=(item_id, status))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert all(success for _, success in results)
        
        # Verify final status
        status = queue_manager.get_queue_status()
        assert len(status['in_progress']) == 5
        assert len(status['completed']) == 5
    
    def test_concurrent_listener_operations(self, queue_manager):
        """Test adding/removing listeners while processing items."""
        listeners = [Mock() for _ in range(5)]
        
        def add_remove_listeners():
            for listener in listeners:
                queue_manager.add_status_listener(listener)
                time.sleep(0.01)  # Small delay
                queue_manager.remove_status_listener(listener)
        
        def enqueue_items():
            for i in range(10):
                queue_manager.enqueue(f"https://youtu.be/test{i}")
                time.sleep(0.01)  # Small delay
        
        # Start both operations concurrently
        thread1 = threading.Thread(target=add_remove_listeners)
        thread2 = threading.Thread(target=enqueue_items)
        
        thread1.start()
        thread2.start()
        
        thread1.join()
        thread2.join()
        
        # Should complete without errors
        status = queue_manager.get_queue_status()
        assert len(status['todo']) == 10


class TestStatisticsAndUtilities:
    """Test statistics tracking and utility methods."""
    
    @pytest.fixture
    def queue_manager(self):
        """Create a QueueManager instance for testing."""
        mock_processor = Mock()
        return QueueManager(mock_processor)
    
    def test_get_statistics_initial(self, queue_manager):
        """Test getting initial statistics."""
        stats = queue_manager.get_statistics()
        
        assert isinstance(stats, dict)
        assert stats['total_processed'] == 0
        assert stats['successful_processed'] == 0
        assert stats['failed_processed'] == 0
        assert stats['queue_size'] == 0
        assert stats['processing_active'] is False
        assert 'uptime_seconds' in stats
        assert 'status_counts' in stats
        assert stats['status_counts']['todo'] == 0
    
    def test_get_statistics_with_items(self, queue_manager):
        """Test getting statistics with items in queue."""
        # Add items in different states
        id1 = queue_manager.enqueue("https://youtu.be/test1")
        id2 = queue_manager.enqueue("https://youtu.be/test2")
        queue_manager.update_item_status(id2, QueueStatus.COMPLETED)
        
        stats = queue_manager.get_statistics()
        
        assert stats['queue_size'] == 2
        assert stats['status_counts']['todo'] == 1
        assert stats['status_counts']['completed'] == 1
    
    def test_clear_completed_items(self, queue_manager):
        """Test clearing old completed items."""
        # Add and complete some items
        id1 = queue_manager.enqueue("https://youtu.be/test1")
        id2 = queue_manager.enqueue("https://youtu.be/test2")
        id3 = queue_manager.enqueue("https://youtu.be/test3")
        
        queue_manager.update_item_status(id1, QueueStatus.COMPLETED)
        queue_manager.update_item_status(id2, QueueStatus.FAILED)
        
        # Manually set old completion time
        item1 = queue_manager.get_item_status(id1)
        item2 = queue_manager.get_item_status(id2)
        old_time = datetime.now() - timedelta(hours=25)
        item1.completed_at = old_time
        item2.completed_at = old_time
        
        # Clear old items
        cleared_count = queue_manager.clear_completed_items(max_age_hours=24)
        
        assert cleared_count == 2
        assert queue_manager.get_item_status(id1) is None
        assert queue_manager.get_item_status(id2) is None
        assert queue_manager.get_item_status(id3) is not None  # Still TODO
    
    def test_clear_completed_items_no_old_items(self, queue_manager):
        """Test clearing when no old items exist."""
        # Add recent completed item
        item_id = queue_manager.enqueue("https://youtu.be/test1")
        queue_manager.update_item_status(item_id, QueueStatus.COMPLETED)
        
        cleared_count = queue_manager.clear_completed_items(max_age_hours=24)
        
        assert cleared_count == 0
        assert queue_manager.get_item_status(item_id) is not None


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.fixture
    def queue_manager(self):
        """Create a QueueManager instance for testing."""
        mock_processor = Mock()
        return QueueManager(mock_processor)
    
    def test_enqueue_with_processing_queue_exception(self, queue_manager):
        """Test handling of internal queue exceptions during enqueue."""
        # Fill the internal processing queue to capacity
        with patch.object(queue_manager._processing_queue, 'put') as mock_put:
            mock_put.side_effect = Exception("Queue error")
            
            with pytest.raises(VideoProcessingError, match="Failed to enqueue item"):
                queue_manager.enqueue("https://youtu.be/test123")
    
    def test_processing_with_video_processor_exception(self, queue_manager):
        """Test handling of VideoProcessor exceptions during processing."""
        queue_manager.video_processor.process_video.side_effect = VideoProcessingError("Processing failed")
        
        queue_manager.start_processing()
        item_id = queue_manager.enqueue("https://youtu.be/test123")
        
        # Wait for processing
        time.sleep(0.2)
        
        item = queue_manager.get_item_status(item_id)
        assert item.status == QueueStatus.FAILED
        assert "Processing failed" in item.error_message
        
        # Check statistics
        stats = queue_manager.get_statistics()
        assert stats['total_processed'] == 1
        assert stats['failed_processed'] == 1
        
        queue_manager.stop_processing()
    
    def test_graceful_shutdown_with_timeout(self, queue_manager):
        """Test graceful shutdown behavior with timeout."""
        # Mock a thread that doesn't stop quickly
        with patch.object(queue_manager, '_processing_thread') as mock_thread:
            mock_thread.is_alive.return_value = True
            mock_thread.join.return_value = None  # Simulate timeout
            
            queue_manager._processing_active = True
            
            success = queue_manager.stop_processing(timeout=0.1)
            
            assert success is False  # Should return False on timeout
            mock_thread.join.assert_called_once_with(timeout=0.1)