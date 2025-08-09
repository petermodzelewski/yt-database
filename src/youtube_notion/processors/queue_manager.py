"""
Queue manager for thread-safe video processing operations.

This module provides a centralized queue management system that supports
both CLI batch processing and web UI modes. It implements thread-safe
operations, observable pattern for real-time updates, and sequential
video processing with proper error handling.
"""

import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any, TYPE_CHECKING
from queue import Queue, Empty
from ..web.models import QueueItem, QueueStatus, ProcessingPhase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..processors.video_processor import VideoProcessor
from ..utils.exceptions import VideoProcessingError, ConfigurationError
from ..utils.chat_logger import ChatLogger


class QueueManager:
    """
    Thread-safe queue manager for video processing operations.
    
    This class provides a centralized queue system that can be used by both
    CLI batch processing and web UI modes. It implements:
    - Thread-safe queue operations using threading.Lock
    - Observable pattern with status change listeners for real-time updates
    - Background processing thread that processes queue items sequentially
    - Graceful shutdown handling for clean application termination
    """
    
    def __init__(self, video_processor: 'VideoProcessor', max_queue_size: int = 100):
        """
        Initialize the queue manager.
        
        Args:
            video_processor: VideoProcessor instance for processing videos
            max_queue_size: Maximum number of items allowed in queue
            
        Raises:
            ConfigurationError: If video_processor is None or invalid
        """
        if not video_processor or not hasattr(video_processor, 'process_video'):
            raise ConfigurationError("VideoProcessor is required")
        
        self.video_processor = video_processor
        self.max_queue_size = max_queue_size
        
        # Thread-safe data structures
        self._lock = threading.RLock()  # Reentrant lock for nested operations
        self._items: Dict[str, QueueItem] = {}
        self._processing_queue: Queue = Queue(maxsize=max_queue_size)
        
        # Status change listeners for observable pattern
        self._status_listeners: List[Callable[[str, QueueItem], None]] = []
        
        # Background processing thread
        self._processing_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._processing_active = False
        
        # Statistics
        self._stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'started_at': datetime.now()
        }
    
    def enqueue(self, url: str, custom_prompt: Optional[str] = None) -> str:
        """
        Add a URL to the processing queue.
        
        Args:
            url: YouTube URL to process
            custom_prompt: Optional custom prompt for summary generation
            
        Returns:
            str: Unique item ID for tracking
            
        Raises:
            ValueError: If URL is invalid or queue is full
            VideoProcessingError: If queue operation fails
        """
        if not url or not isinstance(url, str):
            raise ValueError("URL must be a non-empty string")
        
        # Validate YouTube URL format
        if not self._is_youtube_url(url):
            raise ValueError("URL must be a valid YouTube URL")
        
        with self._lock:
            # Check queue size limit
            if len(self._items) >= self.max_queue_size:
                raise ValueError(f"Queue is full (max {self.max_queue_size} items)")
            
            # Generate unique item ID
            item_id = str(uuid.uuid4())
            
            # Create queue item
            queue_item = QueueItem(
                id=item_id,
                url=url,
                custom_prompt=custom_prompt,
                status=QueueStatus.TODO,
                created_at=datetime.now()
            )
            
            try:
                # Add to internal storage
                self._items[item_id] = queue_item
                
                # Add to processing queue
                self._processing_queue.put(item_id, block=False)
                
                # Notify listeners
                self._notify_status_change(item_id, queue_item)
                
                return item_id
                
            except Exception as e:
                # Clean up on failure
                self._items.pop(item_id, None)
                raise VideoProcessingError(f"Failed to enqueue item: {str(e)}")
    
    def dequeue(self) -> Optional[str]:
        """
        Remove and return the next item ID from the processing queue.
        
        This method is primarily used internally by the processing thread.
        
        Returns:
            Optional[str]: Item ID if available, None if queue is empty
        """
        try:
            return self._processing_queue.get(block=False)
        except Empty:
            return None
    
    def get_queue_status(self) -> Dict[str, List[QueueItem]]:
        """
        Get the current status of all queue items organized by status.
        
        Returns:
            Dict[str, List[QueueItem]]: Items organized by status
                - 'todo': Items waiting to be processed
                - 'in_progress': Items currently being processed
                - 'completed': Successfully processed items
                - 'failed': Items that failed processing
        """
        with self._lock:
            status_groups = {
                'todo': [],
                'in_progress': [],
                'completed': [],
                'failed': []
            }
            
            for item in self._items.values():
                if item.status == QueueStatus.TODO:
                    status_groups['todo'].append(item)
                elif item.status == QueueStatus.IN_PROGRESS:
                    status_groups['in_progress'].append(item)
                elif item.status == QueueStatus.COMPLETED:
                    status_groups['completed'].append(item)
                elif item.status == QueueStatus.FAILED:
                    status_groups['failed'].append(item)
            
            # Sort by creation time (oldest first)
            for status_list in status_groups.values():
                status_list.sort(key=lambda x: x.created_at)
            
            return status_groups
    
    def get_item_status(self, item_id: str) -> Optional[QueueItem]:
        """
        Get the status of a specific queue item.
        
        Args:
            item_id: Unique item identifier
            
        Returns:
            Optional[QueueItem]: Item if found, None otherwise
        """
        with self._lock:
            return self._items.get(item_id)
    
    def update_item_status(self, item_id: str, status: QueueStatus, 
                          error_message: Optional[str] = None,
                          current_phase: Optional[str] = None,
                          current_chunk: Optional[int] = None,
                          total_chunks: Optional[int] = None) -> bool:
        """
        Update the status of a queue item.
        
        Args:
            item_id: Unique item identifier
            status: New status for the item
            error_message: Optional error message for failed items
            current_phase: Optional current processing phase
            current_chunk: Optional current chunk number
            total_chunks: Optional total number of chunks
            
        Returns:
            bool: True if update was successful, False if item not found
        """
        with self._lock:
            item = self._items.get(item_id)
            if not item:
                return False
            
            # Update status and timestamps
            old_status = item.status
            item.status = status
            
            if status == QueueStatus.IN_PROGRESS and old_status == QueueStatus.TODO:
                item.started_at = datetime.now()
            elif status in [QueueStatus.COMPLETED, QueueStatus.FAILED]:
                item.completed_at = datetime.now()
            
            # Update additional fields
            if error_message:
                item.error_message = error_message
            if current_phase:
                item.current_phase = current_phase
            if current_chunk is not None:
                item.current_chunk = current_chunk
            if total_chunks is not None:
                item.total_chunks = total_chunks
            
            # Notify listeners of status change
            self._notify_status_change(item_id, item)
            
            return True
    
    def start_processing(self) -> None:
        """
        Start the background processing thread.
        
        This method starts a background thread that continuously processes
        items from the queue until stop_processing() is called.
        
        Raises:
            RuntimeError: If processing is already active
        """
        with self._lock:
            if self._processing_active:
                raise RuntimeError("Processing is already active")
            
            self._shutdown_event.clear()
            self._processing_active = True
            
            # Start background processing thread
            self._processing_thread = threading.Thread(
                target=self._processing_loop,
                name="QueueManager-ProcessingThread",
                daemon=True
            )
            self._processing_thread.start()
    
    def stop_processing(self, timeout: float = 10.0) -> bool:
        """
        Stop the background processing thread gracefully.
        
        Args:
            timeout: Maximum time to wait for thread to stop (seconds)
            
        Returns:
            bool: True if stopped successfully, False if timeout occurred
        """
        with self._lock:
            if not self._processing_active:
                return True
            
            # Signal shutdown
            self._shutdown_event.set()
            self._processing_active = False
        
        # Wait for thread to finish (outside of lock to avoid deadlock)
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=timeout)
            
            if self._processing_thread.is_alive():
                # Thread didn't stop within timeout
                return False
        
        self._processing_thread = None
        return True
    
    def add_status_listener(self, callback: Callable[[str, QueueItem], None]) -> None:
        """
        Add a status change listener for real-time updates.
        
        Args:
            callback: Function to call when item status changes.
                     Signature: callback(item_id: str, item: QueueItem)
        """
        if not callable(callback):
            raise ValueError("Callback must be callable")
        
        with self._lock:
            if callback not in self._status_listeners:
                self._status_listeners.append(callback)
    
    def remove_status_listener(self, callback: Callable[[str, QueueItem], None]) -> None:
        """
        Remove a status change listener.
        
        Args:
            callback: Function to remove from listeners
        """
        with self._lock:
            if callback in self._status_listeners:
                self._status_listeners.remove(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dict[str, Any]: Statistics including counts and timing information
        """
        with self._lock:
            current_stats = self._stats.copy()
            current_stats.update({
                'queue_size': len(self._items),
                'processing_active': self._processing_active,
                'uptime_seconds': (datetime.now() - self._stats['started_at']).total_seconds()
            })
            
            # Add status breakdown
            status_counts = {'todo': 0, 'in_progress': 0, 'completed': 0, 'failed': 0}
            for item in self._items.values():
                if item.status == QueueStatus.TODO:
                    status_counts['todo'] += 1
                elif item.status == QueueStatus.IN_PROGRESS:
                    status_counts['in_progress'] += 1
                elif item.status == QueueStatus.COMPLETED:
                    status_counts['completed'] += 1
                elif item.status == QueueStatus.FAILED:
                    status_counts['failed'] += 1
            
            # Add both nested and flat format for compatibility
            current_stats['status_counts'] = status_counts
            current_stats.update(status_counts)  # Add flat format
            current_stats['total_items'] = len(self._items)
            return current_stats
    
    def _is_youtube_url(self, url: str) -> bool:
        """
        Check if URL is a valid YouTube URL.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if URL is a valid YouTube URL
        """
        import re
        
        # YouTube URL patterns
        youtube_patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]+)',
            r'(?:https?://)?(?:m\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        ]
        
        for pattern in youtube_patterns:
            if re.match(pattern, url):
                return True
        
        return False
    
    def clear_completed_items(self, max_age_hours: float = 24.0) -> int:
        """
        Clear completed items older than specified age.
        
        Args:
            max_age_hours: Maximum age in hours for completed items
            
        Returns:
            int: Number of items cleared
        """
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        cleared_count = 0
        
        with self._lock:
            items_to_remove = []
            
            for item_id, item in self._items.items():
                if (item.status in [QueueStatus.COMPLETED, QueueStatus.FAILED] and
                    item.completed_at and 
                    item.completed_at.timestamp() < cutoff_time):
                    items_to_remove.append(item_id)
            
            for item_id in items_to_remove:
                del self._items[item_id]
                cleared_count += 1
        
        return cleared_count
    
    def _processing_loop(self) -> None:
        """
        Main processing loop that runs in the background thread.
        
        This method continuously processes items from the queue until
        the shutdown event is set.
        """
        while not self._shutdown_event.is_set():
            try:
                # Get next item to process
                item_id = self.dequeue()
                
                if item_id is None:
                    # No items to process, wait a bit
                    time.sleep(0.1)
                    continue
                
                # Process the item
                self._process_item(item_id)
                
            except Exception as e:
                # Log error but continue processing
                # In a real implementation, you might want to use proper logging
                print(f"Error in processing loop: {str(e)}")
                time.sleep(1)  # Wait before retrying
    
    def _process_item(self, item_id: str) -> None:
        """
        Process a single queue item with enhanced status tracking.
        
        Args:
            item_id: ID of the item to process
        """
        item = self.get_item_status(item_id)
        if not item:
            return
        
        try:
            # Update status to in progress
            self.update_item_status(
                item_id, 
                QueueStatus.IN_PROGRESS,
                current_phase=ProcessingPhase.METADATA_EXTRACTION.value
            )
            
            # Process the video using enhanced VideoProcessor integration
            success = self._process_video_with_callbacks(item_id, item.url, item.custom_prompt)
            
            # Update statistics
            with self._lock:
                self._stats['total_processed'] += 1
                if success:
                    self._stats['successful_processed'] += 1
                else:
                    self._stats['failed_processed'] += 1
            
            # Final status is already set by _process_video_with_callbacks
            # No need to update it again here
                
        except Exception as e:
            # Handle processing errors
            with self._lock:
                self._stats['total_processed'] += 1
                self._stats['failed_processed'] += 1
            
            self.update_item_status(
                item_id,
                QueueStatus.FAILED,
                error_message=f"Processing failed: {str(e)}"
            )
    
    def _process_video_with_callbacks(self, item_id: str, video_url: str, custom_prompt: Optional[str] = None) -> bool:
        """
        Process a video with status update callbacks during each phase.
        
        This method integrates with the existing VideoProcessor while providing
        real-time status updates for the web UI. It handles both regular and
        chunked video processing with appropriate status updates.
        
        Args:
            item_id: Queue item ID for status updates
            video_url: YouTube URL to process
            custom_prompt: Optional custom prompt for summary generation
            
        Returns:
            bool: True if processing completed successfully, False otherwise
        """
        try:
            # Phase 1: Extract metadata
            self.update_item_status(
                item_id,
                QueueStatus.IN_PROGRESS,
                current_phase=ProcessingPhase.METADATA_EXTRACTION.value
            )
            
            metadata = self.video_processor.metadata_extractor.extract_metadata(video_url)
            
            # Update item with video metadata
            item = self.get_item_status(item_id)
            if item:
                item.title = metadata.get("title")
                item.thumbnail_url = metadata.get("thumbnail_url")
                item.channel = metadata.get("channel")
                item.duration = metadata.get("duration")
                self._notify_status_change(item_id, item)
            
            # Check if video needs chunked processing
            duration_seconds = metadata.get('duration', 0)
            from ..config.constants import MAX_VIDEO_DURATION_SECONDS
            from ..utils.video_utils import calculate_video_splits
            
            if duration_seconds > MAX_VIDEO_DURATION_SECONDS:
                # Handle chunked video processing
                return self._process_chunked_video(item_id, video_url, metadata, custom_prompt)
            else:
                # Handle regular video processing
                return self._process_regular_video(item_id, video_url, metadata, custom_prompt)
                
        except Exception as e:
            self.update_item_status(
                item_id,
                QueueStatus.FAILED,
                error_message=f"Processing failed: {str(e)}"
            )
            return False
    
    def _process_regular_video(self, item_id: str, video_url: str, metadata: dict, custom_prompt: Optional[str] = None) -> bool:
        """
        Process a regular (non-chunked) video with status updates.
        
        Args:
            item_id: Queue item ID for status updates
            video_url: YouTube URL to process
            metadata: Video metadata from extraction phase
            custom_prompt: Optional custom prompt for summary generation
            
        Returns:
            bool: True if processing completed successfully, False otherwise
        """
        try:
            # Phase 2: Generate summary
            self.update_item_status(
                item_id,
                QueueStatus.IN_PROGRESS,
                current_phase=ProcessingPhase.SUMMARY_GENERATION.value
            )
            
            summary = self.video_processor.summary_writer.generate_summary(
                video_url, metadata, custom_prompt
            )
            
            # Phase 3: Store in Notion
            self.update_item_status(
                item_id,
                QueueStatus.IN_PROGRESS,
                current_phase=ProcessingPhase.NOTION_UPLOAD.value
            )
            
            # Prepare data for storage
            video_data = {
                "Title": metadata.get("title", "Unknown Title"),
                "Channel": metadata.get("channel", "Unknown Channel"),
                "Video URL": video_url,
                "Cover": metadata.get("thumbnail_url", ""),
                "Summary": summary
            }
            
            # Add additional metadata if available
            if metadata.get("description"):
                video_data["Description"] = metadata["description"]
            if metadata.get("published_at"):
                video_data["Published"] = metadata["published_at"]
            if metadata.get("video_id"):
                video_data["Video ID"] = metadata["video_id"]
            if metadata.get("duration"):
                video_data["Duration"] = metadata["duration"]
            
            success = self.video_processor.storage.store_video_summary(video_data)
            
            # Update chat log path if available
            if hasattr(self.video_processor.summary_writer, 'chat_logger'):
                chat_logger = self.video_processor.summary_writer.chat_logger
                if hasattr(chat_logger, 'get_latest_log_path'):
                    item = self.get_item_status(item_id)
                    if item:
                        item.chat_log_path = chat_logger.get_latest_log_path()
                        self._notify_status_change(item_id, item)
            
            # Update final status based on success
            if success:
                self.update_item_status(item_id, QueueStatus.COMPLETED)
            else:
                self.update_item_status(
                    item_id,
                    QueueStatus.FAILED,
                    error_message="Storage operation failed"
                )
            
            return success
            
        except Exception as e:
            self.update_item_status(
                item_id,
                QueueStatus.FAILED,
                error_message=f"Processing failed: {str(e)}"
            )
            return False
    
    def _process_chunked_video(self, item_id: str, video_url: str, metadata: dict, custom_prompt: Optional[str] = None) -> bool:
        """
        Process a chunked video with detailed status updates for each chunk.
        
        Args:
            item_id: Queue item ID for status updates
            video_url: YouTube URL to process
            metadata: Video metadata from extraction phase
            custom_prompt: Optional custom prompt for summary generation
            
        Returns:
            bool: True if processing completed successfully, False otherwise
        """
        try:
            from ..utils.video_utils import calculate_video_splits
            
            duration_seconds = metadata.get('duration', 0)
            splits = calculate_video_splits(duration_seconds)
            
            # Update item with chunk information
            self.update_item_status(
                item_id,
                QueueStatus.IN_PROGRESS,
                current_phase=ProcessingPhase.CHUNK_PROCESSING.value,
                current_chunk=0,
                total_chunks=len(splits)
            )
            
            # Phase 2: Generate summary for each chunk
            summary = self.video_processor.summary_writer.generate_summary(
                video_url, metadata, custom_prompt
            )
            
            # The GeminiSummaryWriter handles chunked processing internally,
            # but we need to track chunk progress. We'll use a callback approach.
            self._track_chunk_progress(item_id, len(splits))
            
            # Phase 3: Store in Notion
            self.update_item_status(
                item_id,
                QueueStatus.IN_PROGRESS,
                current_phase=ProcessingPhase.NOTION_UPLOAD.value
            )
            
            # Prepare data for storage
            video_data = {
                "Title": metadata.get("title", "Unknown Title"),
                "Channel": metadata.get("channel", "Unknown Channel"),
                "Video URL": video_url,
                "Cover": metadata.get("thumbnail_url", ""),
                "Summary": summary
            }
            
            # Add additional metadata if available
            if metadata.get("description"):
                video_data["Description"] = metadata["description"]
            if metadata.get("published_at"):
                video_data["Published"] = metadata["published_at"]
            if metadata.get("video_id"):
                video_data["Video ID"] = metadata["video_id"]
            if metadata.get("duration"):
                video_data["Duration"] = metadata["duration"]
            
            success = self.video_processor.storage.store_video_summary(video_data)
            
            # Update chunk log paths if available
            if hasattr(self.video_processor.summary_writer, 'chat_logger'):
                chat_logger = self.video_processor.summary_writer.chat_logger
                item = self.get_item_status(item_id)
                if item and hasattr(chat_logger, 'get_chunk_log_paths'):
                    chunk_logs = chat_logger.get_chunk_log_paths(metadata.get('video_id', 'unknown'))
                    item.chunk_logs = chunk_logs
                    self._notify_status_change(item_id, item)
            
            # Update final status based on success
            if success:
                self.update_item_status(item_id, QueueStatus.COMPLETED)
            else:
                self.update_item_status(
                    item_id,
                    QueueStatus.FAILED,
                    error_message="Storage operation failed"
                )
            
            return success
            
        except Exception as e:
            self.update_item_status(
                item_id,
                QueueStatus.FAILED,
                error_message=f"Processing failed: {str(e)}"
            )
            return False
    
    def _track_chunk_progress(self, item_id: str, total_chunks: int) -> None:
        """
        Track chunk processing progress.
        
        Since the GeminiSummaryWriter handles chunked processing internally,
        we'll update the status to show that chunked processing is happening.
        The actual chunk progress is visible through the console output from
        GeminiSummaryWriter.
        
        Args:
            item_id: Queue item ID for status updates
            total_chunks: Total number of chunks being processed
        """
        # Update status to show chunked processing is happening
        self.update_item_status(
            item_id,
            QueueStatus.IN_PROGRESS,
            current_phase=ProcessingPhase.CHUNK_PROCESSING.value,
            current_chunk=1,
            total_chunks=total_chunks
        )
    
    def _notify_status_change(self, item_id: str, item: QueueItem) -> None:
        """
        Notify all registered listeners of a status change.
        
        Args:
            item_id: ID of the item that changed
            item: The updated queue item
        """
        # Create a copy of listeners to avoid issues with concurrent modification
        with self._lock:
            listeners = self._status_listeners.copy()
        
        # Call listeners outside of lock to avoid deadlocks
        for listener in listeners:
            try:
                listener(item_id, item)
            except Exception as e:
                # Log error but don't let it affect other listeners
                # In a real implementation, you might want to use proper logging
                print(f"Error in status listener: {str(e)}")
    
    def __enter__(self):
        """Context manager entry."""
        self.start_processing()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with graceful shutdown."""
        self.stop_processing()