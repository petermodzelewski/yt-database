"""
FastAPI web server for the YouTube-to-Notion web UI.

This module provides the HTTP server for serving the web UI and handling
API requests. It includes endpoints for queue management, status monitoring,
and chat log retrieval, along with static file serving and CORS support.
"""

import asyncio
import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError

from .config import WebServerConfig
from .models import (
    AddUrlRequest, AddUrlResponse, QueueStatusResponse, QueueItemResponse,
    ErrorResponse, ErrorCodes, QueueItem
)

if TYPE_CHECKING:
    from ..processors.queue_manager import QueueManager

from ..utils.exceptions import VideoProcessingError, ConfigurationError


class WebServer:
    """
    FastAPI web server for the YouTube-to-Notion web UI.
    
    This class provides:
    - RESTful API endpoints with automatic OpenAPI documentation
    - Server-Sent Events (SSE) for real-time updates
    - Static file serving for frontend assets
    - Built-in CORS middleware
    - Automatic request/response validation with Pydantic
    """
    
    def __init__(self, queue_manager: 'QueueManager', config: Optional[WebServerConfig] = None):
        """
        Initialize the web server.
        
        Args:
            queue_manager: QueueManager instance for handling video processing
            config: Optional configuration, defaults to environment-based config
            
        Raises:
            ConfigurationError: If queue_manager is None or invalid
        """
        if not queue_manager:
            raise ConfigurationError("QueueManager is required")
        
        self.queue_manager = queue_manager
        self.config = config or WebServerConfig.from_env()
        
        # FastAPI application
        self.app = FastAPI(
            title="YouTube-to-Notion Web UI",
            description="Web interface for managing YouTube video processing queue",
            version="1.0.0",
            debug=self.config.debug
        )
        
        # Server state
        self._server_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()
        self._running = False
        
        # SSE connections for real-time updates
        self._sse_connections: List[asyncio.Queue] = []
        self._sse_lock = threading.Lock()
        
        # Setup FastAPI application
        self._setup_middleware()
        self._setup_routes()
        self._setup_static_files()
        self._setup_queue_listener()
    
    def _setup_middleware(self) -> None:
        """Setup CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["*"],
        )
    
    def _setup_routes(self) -> None:
        """Setup API routes."""
        
        @self.app.post("/api/queue", response_model=AddUrlResponse)
        async def add_url_endpoint(request: AddUrlRequest) -> AddUrlResponse:
            """
            Add a URL to the processing queue.
            
            Args:
                request: URL and optional custom prompt
                
            Returns:
                AddUrlResponse: Success status and item ID or error message
            """
            try:
                # Convert Pydantic HttpUrl to string
                url_str = str(request.url)
                
                # Add to queue
                item_id = self.queue_manager.enqueue(url_str, request.custom_prompt)
                
                return AddUrlResponse(
                    success=True,
                    item_id=item_id
                )
                
            except ValueError as e:
                return AddUrlResponse(
                    success=False,
                    error=str(e)
                )
            except VideoProcessingError as e:
                return AddUrlResponse(
                    success=False,
                    error=f"Processing error: {str(e)}"
                )
            except Exception as e:
                return AddUrlResponse(
                    success=False,
                    error=f"Server error: {str(e)}"
                )
        
        @self.app.get("/api/status", response_model=QueueStatusResponse)
        async def get_status_endpoint() -> QueueStatusResponse:
            """
            Get current queue status organized by processing state.
            
            Returns:
                QueueStatusResponse: Items organized by status (todo, in_progress, completed, failed)
            """
            try:
                status_dict = self.queue_manager.get_queue_status()
                
                # Convert QueueItem dataclasses to Pydantic models
                return QueueStatusResponse(
                    todo=[QueueItemResponse.from_queue_item(item) for item in status_dict['todo']],
                    in_progress=[QueueItemResponse.from_queue_item(item) for item in status_dict['in_progress']],
                    completed=[QueueItemResponse.from_queue_item(item) for item in status_dict['completed']],
                    failed=[QueueItemResponse.from_queue_item(item) for item in status_dict['failed']]
                )
                
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get queue status: {str(e)}"
                )
        
        @self.app.get("/api/chat-log/{item_id}")
        async def get_chat_log_endpoint(item_id: str) -> dict:
            """
            Retrieve chat log for a specific queue item.
            
            Args:
                item_id: Unique identifier for the queue item
                
            Returns:
                dict: Chat log content and metadata
                
            Raises:
                HTTPException: If item not found or chat log unavailable
            """
            try:
                # Get item from queue
                item = self.queue_manager.get_item_status(item_id)
                if not item:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Item {item_id} not found"
                    )
                
                # Check if chat log exists
                if not item.chat_log_path:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Chat log not available for item {item_id}"
                    )
                
                # Read chat log file
                chat_log_path = Path(item.chat_log_path)
                if not chat_log_path.exists():
                    raise HTTPException(
                        status_code=404,
                        detail=f"Chat log file not found: {item.chat_log_path}"
                    )
                
                try:
                    with open(chat_log_path, 'r', encoding='utf-8') as f:
                        chat_content = f.read()
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to read chat log: {str(e)}"
                    )
                
                return {
                    "item_id": item_id,
                    "url": item.url,
                    "title": item.title,
                    "chat_log": chat_content,
                    "chunk_logs": item.chunk_logs,
                    "created_at": item.created_at.isoformat(),
                    "completed_at": item.completed_at.isoformat() if item.completed_at else None
                }
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Server error: {str(e)}"
                )
        
        @self.app.get("/events")
        async def sse_endpoint(request: Request) -> StreamingResponse:
            """
            Server-Sent Events endpoint for real-time queue updates.
            
            Args:
                request: FastAPI request object for connection management
                
            Returns:
                StreamingResponse: SSE stream with queue status updates
            """
            async def event_stream():
                # Create a queue for this connection
                connection_queue = asyncio.Queue()
                
                # Add to active connections
                with self._sse_lock:
                    self._sse_connections.append(connection_queue)
                
                try:
                    # Send initial queue status
                    initial_status = self.queue_manager.get_queue_status()
                    initial_data = {
                        "type": "queue_status",
                        "data": {
                            "todo": [self._queue_item_to_dict(item) for item in initial_status['todo']],
                            "in_progress": [self._queue_item_to_dict(item) for item in initial_status['in_progress']],
                            "completed": [self._queue_item_to_dict(item) for item in initial_status['completed']],
                            "failed": [self._queue_item_to_dict(item) for item in initial_status['failed']]
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(initial_data)}\n\n"
                    
                    # Send periodic updates
                    while True:
                        try:
                            # Wait for events with timeout for heartbeat
                            event_data = await asyncio.wait_for(
                                connection_queue.get(),
                                timeout=self.config.sse_heartbeat_interval
                            )
                            yield f"data: {json.dumps(event_data)}\n\n"
                            
                        except asyncio.TimeoutError:
                            # Send heartbeat
                            heartbeat = {
                                "type": "heartbeat",
                                "timestamp": datetime.now().isoformat()
                            }
                            yield f"data: {json.dumps(heartbeat)}\n\n"
                            
                        except asyncio.CancelledError:
                            break
                            
                except Exception as e:
                    # Send error event
                    error_event = {
                        "type": "error",
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                    yield f"data: {json.dumps(error_event)}\n\n"
                    
                finally:
                    # Remove from active connections
                    with self._sse_lock:
                        if connection_queue in self._sse_connections:
                            self._sse_connections.remove(connection_queue)
            
            return StreamingResponse(
                event_stream(),
                media_type='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Cache-Control'
                }
            )
        
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            stats = self.queue_manager.get_statistics()
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "queue_stats": stats
            }
    
    def _setup_static_files(self) -> None:
        """Setup static file serving for frontend assets."""
        static_path = Path(self.config.static_folder)
        
        # Create static directory if it doesn't exist
        static_path.mkdir(parents=True, exist_ok=True)
        
        # Mount static files
        if static_path.exists():
            self.app.mount("/static", StaticFiles(directory=str(static_path)), name="static")
        
        # Serve index.html at root
        @self.app.get("/")
        async def serve_index():
            """Serve the main HTML file."""
            index_path = static_path / "index.html"
            if index_path.exists():
                return FileResponse(str(index_path))
            else:
                return {"message": "Web UI not yet implemented. Static files not found."}
    
    def _setup_queue_listener(self) -> None:
        """Setup listener for queue status changes."""
        def on_status_change(item_id: str, item: QueueItem) -> None:
            """Handle queue status changes and broadcast to SSE connections."""
            event_data = {
                "type": "status_change",
                "data": {
                    "item_id": item_id,
                    "item": self._queue_item_to_dict(item)
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Broadcast to all SSE connections
            self._broadcast_sse_event(event_data)
        
        # Register the listener
        self.queue_manager.add_status_listener(on_status_change)
    
    def _queue_item_to_dict(self, item: QueueItem) -> dict:
        """Convert QueueItem to dictionary for JSON serialization."""
        return {
            "id": item.id,
            "url": item.url,
            "custom_prompt": item.custom_prompt,
            "status": item.status.value,
            "title": item.title,
            "thumbnail_url": item.thumbnail_url,
            "channel": item.channel,
            "created_at": item.created_at.isoformat(),
            "started_at": item.started_at.isoformat() if item.started_at else None,
            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
            "error_message": item.error_message,
            "chat_log_path": item.chat_log_path,
            "chunk_logs": item.chunk_logs,
            "current_phase": item.current_phase,
            "current_chunk": item.current_chunk,
            "total_chunks": item.total_chunks
        }
    
    def _broadcast_sse_event(self, event_data: dict) -> None:
        """Broadcast event to all SSE connections."""
        with self._sse_lock:
            # Remove closed connections and send to active ones
            active_connections = []
            for connection_queue in self._sse_connections:
                try:
                    connection_queue.put_nowait(event_data)
                    active_connections.append(connection_queue)
                except asyncio.QueueFull:
                    # Connection queue is full, skip this connection
                    pass
                except Exception:
                    # Connection is likely closed, don't add to active list
                    pass
            
            # Update active connections list
            self._sse_connections = active_connections
    
    def start(self) -> None:
        """
        Start the web server.
        
        This method starts the FastAPI server using uvicorn in a separate thread.
        
        Raises:
            RuntimeError: If server is already running
        """
        if self._running:
            raise RuntimeError("Server is already running")
        
        self._shutdown_event.clear()
        self._running = True
        
        # Start server in a separate thread
        self._server_thread = threading.Thread(
            target=self._run_server,
            name="WebServer-Thread",
            daemon=True
        )
        self._server_thread.start()
    
    def stop(self, timeout: float = 10.0) -> bool:
        """
        Stop the web server gracefully.
        
        Args:
            timeout: Maximum time to wait for server to stop (seconds)
            
        Returns:
            bool: True if stopped successfully, False if timeout occurred
        """
        if not self._running:
            return True
        
        # Signal shutdown
        self._shutdown_event.set()
        self._running = False
        
        # Wait for server thread to finish
        if self._server_thread and self._server_thread.is_alive():
            self._server_thread.join(timeout=timeout)
            
            if self._server_thread.is_alive():
                return False
        
        self._server_thread = None
        return True
    
    def _run_server(self) -> None:
        """Run the uvicorn server."""
        try:
            uvicorn.run(
                self.app,
                host=self.config.host,
                port=self.config.port,
                reload=self.config.reload,
                log_level="info" if self.config.debug else "warning"
            )
        except Exception as e:
            print(f"Server error: {str(e)}")
        finally:
            self._running = False
    
    @property
    def is_running(self) -> bool:
        """Check if the server is currently running."""
        return self._running
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with graceful shutdown."""
        self.stop()