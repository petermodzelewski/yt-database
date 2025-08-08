/**
 * Queue Columns Component
 * 
 * Component for managing the three-column queue layout
 */

class QueueColumns {
    constructor() {
        this.columns = {
            todo: DOMUtils.getElementById('todo-items'),
            'in-progress': DOMUtils.getElementById('in-progress-items'),
            done: DOMUtils.getElementById('done-items')
        };
        
        this.counters = {
            todo: DOMUtils.getElementById('todo-count'),
            'in-progress': DOMUtils.getElementById('in-progress-count'),
            done: DOMUtils.getElementById('done-count')
        };
        
        this.init();
    }

    init() {
        // Initialize empty state
        this.render({ todo: [], 'in-progress': [], done: [] });
    }

    /**
     * Render queue data in columns
     * @param {Object} queueData - Queue data organized by status
     */
    render(queueData) {
        Object.entries(queueData).forEach(([status, items]) => {
            const column = this.columns[status];
            const counter = this.counters[status];
            
            if (column) {
                // Clear existing content
                column.innerHTML = '';
                
                // Add items
                items.forEach(item => {
                    const itemElement = this.createQueueItemElement(item);
                    column.appendChild(itemElement);
                });
                
                // Update counter
                if (counter) {
                    counter.textContent = items.length.toString();
                }
            }
        });
        
        // Update total stats
        this.updateStats(queueData);
    }

    /**
     * Create a queue item DOM element
     * @param {Object} item - Queue item data
     * @returns {HTMLElement}
     */
    createQueueItemElement(item) {
        const itemElement = DOMUtils.createElement('div', {
            className: `queue-item ${item.status}`,
            dataset: { itemId: item.id }
        });

        // Item header with thumbnail and info
        const header = DOMUtils.createElement('div', { className: 'item-header' });
        
        const thumbnail = DOMUtils.createElement('div', { className: 'item-thumbnail' });
        if (item.thumbnail_url) {
            const img = DOMUtils.createElement('img', {
                src: item.thumbnail_url,
                alt: 'Video thumbnail',
                loading: 'lazy'
            });
            
            // Handle image load errors with fallback
            img.addEventListener('error', () => {
                thumbnail.innerHTML = '';
                thumbnail.appendChild(DOMUtils.createElement('div', { 
                    className: 'thumbnail-placeholder' 
                }, '📺'));
            });
            
            thumbnail.appendChild(img);
        } else {
            thumbnail.appendChild(DOMUtils.createElement('div', { 
                className: 'thumbnail-placeholder' 
            }, item.title ? '📺' : '⏳'));
        }
        
        const info = DOMUtils.createElement('div', { className: 'item-info' });
        info.appendChild(DOMUtils.createElement('div', { className: 'item-title' }, item.title || 'Loading...'));
        info.appendChild(DOMUtils.createElement('div', { className: 'item-channel' }, item.channel || ''));
        info.appendChild(DOMUtils.createElement('div', { className: 'item-duration' }, this.formatDuration(item.duration)));
        
        header.appendChild(thumbnail);
        header.appendChild(info);
        itemElement.appendChild(header);

        // Item status
        const status = DOMUtils.createElement('div', { className: 'item-status' });
        const statusText = DOMUtils.createElement('span', { className: 'status-text' });
        const statusIcon = DOMUtils.createElement('span', { className: `status-icon ${item.status}` });
        statusText.appendChild(statusIcon);
        statusText.appendChild(document.createTextNode(this.getStatusText(item)));
        status.appendChild(statusText);
        itemElement.appendChild(status);

        // Progress bar for in-progress items
        if (item.status === 'in_progress') {
            const progressBar = this.createProgressBar(item);
            itemElement.appendChild(progressBar);
        }

        // Action buttons for completed items
        if (item.status === 'completed') {
            const actions = this.createActionButtons(item);
            if (actions) {
                itemElement.appendChild(actions);
            }
        }

        return itemElement;
    }

    /**
     * Get human-readable status text
     * @param {Object} item - Queue item
     * @returns {string}
     */
    getStatusText(item) {
        switch (item.status) {
            case 'todo':
                return 'Waiting in queue';
            case 'in_progress':
                let statusText = item.current_phase || 'Processing...';
                
                // Add chunk indicator for chunked videos
                if (item.current_chunk && item.total_chunks) {
                    statusText += ` (chunk ${item.current_chunk}/${item.total_chunks})`;
                }
                
                return statusText;
            case 'completed':
                return 'Completed successfully';
            case 'failed':
                return item.error_message || 'Processing failed';
            default:
                return 'Unknown status';
        }
    }

    /**
     * Create progress bar element
     * @param {Object} item - Queue item
     * @returns {HTMLElement}
     */
    createProgressBar(item) {
        const progress = this.calculateProgress(item);
        const progressBar = DOMUtils.createElement('div', { className: 'progress-bar' });
        const progressFill = DOMUtils.createElement('div', { 
            className: 'progress-fill',
            style: `width: ${progress}%`
        });
        progressBar.appendChild(progressFill);
        return progressBar;
    }

    /**
     * Calculate progress percentage based on current phase
     * @param {Object} item - Queue item
     * @returns {number}
     */
    calculateProgress(item) {
        const currentPhase = item.current_phase || '';
        
        // Handle chunked video progress
        if (item.current_chunk && item.total_chunks) {
            const chunkProgress = (item.current_chunk - 1) / item.total_chunks * 100;
            
            // Add phase progress within current chunk
            let phaseProgress = 0;
            if (currentPhase.includes('metadata')) phaseProgress = 10;
            else if (currentPhase.includes('summary') || currentPhase.includes('chunk')) phaseProgress = 60;
            else if (currentPhase.includes('upload')) phaseProgress = 90;
            
            const chunkSize = 100 / item.total_chunks;
            return Math.min(95, chunkProgress + (phaseProgress / 100) * chunkSize);
        }
        
        // Handle regular video progress
        if (currentPhase.includes('metadata')) return 25;
        if (currentPhase.includes('summary')) return 50;
        if (currentPhase.includes('upload')) return 75;
        return 10; // Default progress
    }

    /**
     * Format duration in seconds to human-readable format
     * @param {number|null} duration - Duration in seconds
     * @returns {string} Formatted duration string
     */
    formatDuration(duration) {
        if (!duration || duration <= 0) return '';
        
        const hours = Math.floor(duration / 3600);
        const minutes = Math.floor((duration % 3600) / 60);
        const seconds = duration % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
    }

    /**
     * Create action buttons for completed items
     * @param {Object} item - Queue item
     * @returns {HTMLElement|null}
     */
    createActionButtons(item) {
        const buttons = [];
        
        // Main chat log button
        if (item.chat_log_path) {
            const viewLogBtn = DOMUtils.createElement('button', {
                className: 'action-btn primary'
            }, '👁 View Log');
            
            DOMUtils.addEventListener(viewLogBtn, 'click', () => {
                window.app.showChatLog(item.id);
            });
            
            buttons.push(viewLogBtn);
        }
        
        // Chunk log buttons
        if (item.chunk_logs && item.chunk_logs.length > 0) {
            item.chunk_logs.forEach((log, index) => {
                const chunkBtn = DOMUtils.createElement('button', {
                    className: 'action-btn'
                }, `👁 ${index + 1}`);
                
                DOMUtils.addEventListener(chunkBtn, 'click', () => {
                    window.app.showChatLog(item.id, index);
                });
                
                buttons.push(chunkBtn);
            });
        }
        
        if (buttons.length === 0) return null;
        
        const actionsContainer = DOMUtils.createElement('div', { className: 'item-actions' });
        buttons.forEach(button => actionsContainer.appendChild(button));
        
        return actionsContainer;
    }

    /**
     * Update header statistics
     * @param {Object} queueData - Queue data
     */
    updateStats(queueData) {
        const totalCount = DOMUtils.getElementById('total-count');
        const processingCount = DOMUtils.getElementById('processing-count');
        
        if (totalCount) {
            const total = Object.values(queueData).reduce((sum, items) => sum + items.length, 0);
            totalCount.textContent = total.toString();
        }
        
        if (processingCount) {
            const processing = queueData['in-progress'] ? queueData['in-progress'].length : 0;
            processingCount.textContent = processing.toString();
        }
    }

    /**
     * Animate item movement between columns
     * @param {string} itemId - Item ID
     * @param {string} fromStatus - Source status
     * @param {string} toStatus - Target status
     */
    async moveItem(itemId, fromStatus, toStatus) {
        const fromColumn = this.columns[fromStatus];
        const toColumn = this.columns[toStatus];
        const item = fromColumn?.querySelector(`[data-item-id="${itemId}"]`);
        
        if (!item || !toColumn) return;
        
        // Animate fade out
        await DOMUtils.animate(item, { opacity: '0', transform: 'translateX(20px)' });
        
        // Move to new column
        toColumn.appendChild(item);
        
        // Animate fade in
        item.style.opacity = '0';
        item.style.transform = 'translateX(-20px)';
        await DOMUtils.animate(item, { opacity: '1', transform: 'translateX(0)' });
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QueueColumns;
}

// Make available globally
window.QueueColumns = QueueColumns;