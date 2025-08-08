/**
 * SSE Connection Component
 * 
 * Manages Server-Sent Events connection for real-time queue updates.
 * Handles connection management, automatic reconnection, and event processing.
 */

class SSEConnection {
    constructor(app) {
        this.app = app;
        this.eventSource = null;
        this.isConnected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000; // Start with 1 second
        this.maxReconnectDelay = 30000; // Max 30 seconds
        this.reconnectTimer = null;
        this.heartbeatTimer = null;
        this.lastHeartbeat = null;
        
        // Event handlers
        this.eventHandlers = {
            'queue_status': this.handleQueueStatus.bind(this),
            'status_change': this.handleStatusChange.bind(this),
            'heartbeat': this.handleHeartbeat.bind(this),
            'error': this.handleError.bind(this)
        };
        
        this.init();
    }

    /**
     * Initialize the SSE connection
     */
    init() {
        console.log('SSEConnection: Initializing');
        this.connect();
    }

    /**
     * Establish SSE connection to the server
     */
    connect() {
        if (this.eventSource) {
            this.disconnect();
        }

        console.log('SSEConnection: Connecting to /events');
        
        try {
            this.eventSource = new EventSource('/events');
            
            // Setup event listeners
            this.eventSource.onopen = this.handleOpen.bind(this);
            this.eventSource.onmessage = this.handleMessage.bind(this);
            this.eventSource.onerror = this.handleConnectionError.bind(this);
            
            // Start heartbeat monitoring
            this.startHeartbeatMonitoring();
            
        } catch (error) {
            console.error('SSEConnection: Failed to create EventSource:', error);
            this.scheduleReconnect();
        }
    }

    /**
     * Disconnect from SSE server
     */
    disconnect() {
        console.log('SSEConnection: Disconnecting');
        
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
        
        this.isConnected = false;
        this.clearReconnectTimer();
        this.clearHeartbeatTimer();
    }

    /**
     * Handle successful connection
     */
    handleOpen(event) {
        console.log('SSEConnection: Connected successfully');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000; // Reset delay
        this.lastHeartbeat = Date.now();
        
        // Update UI connection status
        this.updateConnectionStatus(true);
    }

    /**
     * Handle incoming SSE messages
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('SSEConnection: Received event:', data.type, data);
            
            // Update last heartbeat time
            this.lastHeartbeat = Date.now();
            
            // Route to appropriate handler
            const handler = this.eventHandlers[data.type];
            if (handler) {
                handler(data);
            } else {
                console.warn('SSEConnection: Unknown event type:', data.type);
            }
            
        } catch (error) {
            console.error('SSEConnection: Failed to parse message:', error, event.data);
        }
    }

    /**
     * Handle connection errors
     */
    handleConnectionError(event) {
        console.error('SSEConnection: Connection error:', event);
        this.isConnected = false;
        this.updateConnectionStatus(false);
        
        // Only attempt reconnection if not explicitly closed
        if (this.eventSource && this.eventSource.readyState !== EventSource.CLOSED) {
            this.scheduleReconnect();
        }
    }

    /**
     * Handle queue status updates
     */
    handleQueueStatus(data) {
        console.log('SSEConnection: Handling queue status update');
        
        if (data.data && this.app) {
            // Transform status keys to match frontend expectations
            const queueData = {
                'todo': data.data.todo || [],
                'in-progress': data.data.in_progress || [],
                'done': data.data.completed || []
            };
            
            // Update UI with smooth transition
            this.app.updateQueueDisplay(queueData);
        }
    }

    /**
     * Handle individual item status changes
     */
    handleStatusChange(data) {
        console.log('SSEConnection: Handling status change for item:', data.data.item_id);
        
        if (data.data && data.data.item && this.app) {
            const item = data.data.item;
            const itemId = data.data.item_id;
            
            // Determine old and new status for animation
            const newStatus = this.mapStatusToColumn(item.status);
            const oldStatus = this.findItemCurrentColumn(itemId);
            
            if (oldStatus && oldStatus !== newStatus) {
                // Animate item movement between columns
                this.animateItemMovement(itemId, oldStatus, newStatus, item);
            } else {
                // Update item in place
                this.updateItemInPlace(itemId, item);
            }
        }
    }

    /**
     * Handle heartbeat messages
     */
    handleHeartbeat(data) {
        // Heartbeat received, connection is alive
        this.lastHeartbeat = Date.now();
    }

    /**
     * Handle error messages from server
     */
    handleError(data) {
        console.error('SSEConnection: Server error:', data.error);
        // Could show user notification here
    }

    /**
     * Map server status to frontend column names
     */
    mapStatusToColumn(status) {
        const statusMap = {
            'todo': 'todo',
            'in_progress': 'in-progress',
            'completed': 'done',
            'failed': 'done' // Failed items go to done column
        };
        return statusMap[status] || 'todo';
    }

    /**
     * Find which column currently contains an item
     */
    findItemCurrentColumn(itemId) {
        const columns = ['todo', 'in-progress', 'done'];
        
        for (const column of columns) {
            const columnElement = document.getElementById(`${column}-items`);
            if (columnElement && columnElement.querySelector(`[data-item-id="${itemId}"]`)) {
                return column;
            }
        }
        
        return null;
    }

    /**
     * Animate item movement between columns
     */
    async animateItemMovement(itemId, fromColumn, toColumn, itemData) {
        console.log(`SSEConnection: Animating item ${itemId} from ${fromColumn} to ${toColumn}`);
        
        const fromColumnElement = document.getElementById(`${fromColumn}-items`);
        const toColumnElement = document.getElementById(`${toColumn}-items`);
        const itemElement = fromColumnElement?.querySelector(`[data-item-id="${itemId}"]`);
        
        if (!itemElement || !toColumnElement) {
            // Fallback to full refresh if animation fails
            this.refreshQueueStatus();
            return;
        }
        
        try {
            // Phase 1: Fade out and slide right
            await DOMUtils.animate(itemElement, {
                opacity: '0',
                transform: 'translateX(20px) scale(0.95)'
            }, 300);
            
            // Phase 2: Remove from old column and create new element
            const queueColumns = this.app.getComponent('queueColumns');
            if (queueColumns) {
                // Create updated item element
                const newItemElement = queueColumns.createQueueItemElement(itemData);
                
                // Add to new column (initially hidden)
                newItemElement.style.opacity = '0';
                newItemElement.style.transform = 'translateX(-20px) scale(0.95)';
                toColumnElement.appendChild(newItemElement);
                
                // Remove old element
                itemElement.remove();
                
                // Phase 3: Fade in and slide to position
                await DOMUtils.animate(newItemElement, {
                    opacity: '1',
                    transform: 'translateX(0) scale(1)'
                }, 300);
                
                // Update counters
                this.updateColumnCounters();
            }
            
        } catch (error) {
            console.error('SSEConnection: Animation failed:', error);
            // Fallback to full refresh
            this.refreshQueueStatus();
        }
    }

    /**
     * Update item in place without moving columns
     */
    updateItemInPlace(itemId, itemData) {
        console.log(`SSEConnection: Updating item ${itemId} in place`);
        
        const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
        if (!itemElement) {
            // Item not found, refresh queue
            this.refreshQueueStatus();
            return;
        }
        
        const queueColumns = this.app.getComponent('queueColumns');
        if (queueColumns) {
            // Create new element
            const newItemElement = queueColumns.createQueueItemElement(itemData);
            
            // Replace old element with smooth transition
            itemElement.style.transition = 'opacity 0.2s ease';
            itemElement.style.opacity = '0.5';
            
            setTimeout(() => {
                itemElement.replaceWith(newItemElement);
                newItemElement.style.opacity = '0.5';
                newItemElement.style.transition = 'opacity 0.2s ease';
                
                setTimeout(() => {
                    newItemElement.style.opacity = '1';
                }, 50);
            }, 100);
        }
    }

    /**
     * Update column counters after item movement
     */
    updateColumnCounters() {
        const columns = ['todo', 'in-progress', 'done'];
        
        columns.forEach(column => {
            const columnElement = document.getElementById(`${column}-items`);
            const counterElement = document.getElementById(`${column}-count`);
            
            if (columnElement && counterElement) {
                const itemCount = columnElement.querySelectorAll('.queue-item').length;
                counterElement.textContent = itemCount.toString();
            }
        });
        
        // Update header stats
        const totalCount = document.getElementById('total-count');
        const processingCount = document.getElementById('processing-count');
        
        if (totalCount) {
            const total = document.querySelectorAll('.queue-item').length;
            totalCount.textContent = total.toString();
        }
        
        if (processingCount) {
            const processing = document.querySelectorAll('#in-progress-items .queue-item').length;
            processingCount.textContent = processing.toString();
        }
    }

    /**
     * Schedule reconnection attempt
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('SSEConnection: Max reconnection attempts reached');
            this.updateConnectionStatus(false, 'Connection failed after multiple attempts');
            return;
        }
        
        this.clearReconnectTimer();
        
        console.log(`SSEConnection: Scheduling reconnect attempt ${this.reconnectAttempts + 1} in ${this.reconnectDelay}ms`);
        
        this.reconnectTimer = setTimeout(() => {
            this.reconnectAttempts++;
            this.connect();
            
            // Exponential backoff with jitter
            this.reconnectDelay = Math.min(
                this.reconnectDelay * 2 + Math.random() * 1000,
                this.maxReconnectDelay
            );
        }, this.reconnectDelay);
    }

    /**
     * Clear reconnection timer
     */
    clearReconnectTimer() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
    }

    /**
     * Start heartbeat monitoring
     */
    startHeartbeatMonitoring() {
        this.clearHeartbeatTimer();
        
        this.heartbeatTimer = setInterval(() => {
            const now = Date.now();
            const timeSinceLastHeartbeat = now - (this.lastHeartbeat || now);
            
            // If no heartbeat for 60 seconds, consider connection dead
            if (timeSinceLastHeartbeat > 60000) {
                console.warn('SSEConnection: No heartbeat received, reconnecting');
                this.handleConnectionError(new Event('heartbeat_timeout'));
            }
        }, 30000); // Check every 30 seconds
    }

    /**
     * Clear heartbeat timer
     */
    clearHeartbeatTimer() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    /**
     * Update connection status in UI
     */
    updateConnectionStatus(connected, message = null) {
        // Add connection indicator to header if it doesn't exist
        let indicator = document.getElementById('connection-indicator');
        if (!indicator) {
            indicator = DOMUtils.createElement('div', {
                id: 'connection-indicator',
                className: 'connection-indicator'
            });
            
            const headerStats = document.querySelector('.header-stats');
            if (headerStats) {
                headerStats.appendChild(indicator);
            }
        }
        
        // Update indicator
        if (connected) {
            indicator.className = 'connection-indicator connected';
            indicator.innerHTML = '<span class="status-dot"></span>Connected';
        } else {
            indicator.className = 'connection-indicator disconnected';
            indicator.innerHTML = '<span class="status-dot"></span>' + (message || 'Disconnected');
        }
    }

    /**
     * Refresh queue status from server
     */
    async refreshQueueStatus() {
        try {
            const response = await fetch('/api/status');
            if (response.ok) {
                const data = await response.json();
                
                // Transform to expected format
                const queueData = {
                    'todo': data.todo || [],
                    'in-progress': data.in_progress || [],
                    'done': data.completed || []
                };
                
                this.app.updateQueueDisplay(queueData);
            }
        } catch (error) {
            console.error('SSEConnection: Failed to refresh queue status:', error);
        }
    }

    /**
     * Manually trigger reconnection
     */
    reconnect() {
        console.log('SSEConnection: Manual reconnection triggered');
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        this.disconnect();
        this.connect();
    }

    /**
     * Get connection statistics
     */
    getStats() {
        return {
            isConnected: this.isConnected,
            reconnectAttempts: this.reconnectAttempts,
            lastHeartbeat: this.lastHeartbeat,
            timeSinceLastHeartbeat: this.lastHeartbeat ? Date.now() - this.lastHeartbeat : null
        };
    }

    /**
     * Cleanup when component is destroyed
     */
    destroy() {
        console.log('SSEConnection: Destroying');
        this.disconnect();
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SSEConnection;
}

// Make available globally
window.SSEConnection = SSEConnection;