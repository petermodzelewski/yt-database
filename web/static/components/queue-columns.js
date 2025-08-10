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

        // Action buttons for completed and failed items
        if (item.status === 'completed' || item.status === 'failed') {
            const actions = this.createActionButtons(item);
            if (actions) {
                itemElement.appendChild(actions);
            }
        }

        // Error details for failed items
        if (item.status === 'failed' && item.error_message) {
            const errorDetails = this.createErrorDetails(item);
            if (errorDetails) {
                itemElement.appendChild(errorDetails);
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
                return this.getErrorDisplayText(item.error_message);
            default:
                return 'Unknown status';
        }
    }

    /**
     * Get user-friendly error display text with troubleshooting context
     * @param {string|null} errorMessage - Raw error message from server
     * @returns {string} User-friendly error message
     */
    getErrorDisplayText(errorMessage) {
        if (!errorMessage) {
            return 'Processing failed - Unknown error';
        }

        // Map common error patterns to user-friendly messages
        const errorMappings = [
            {
                pattern: /invalid.*url|invalid.*format|url.*not.*valid/i,
                message: 'URL is not valid',
                context: 'Please check the URL format'
            },
            {
                pattern: /network.*error|connection.*error|timeout/i,
                message: 'network connection failed',
                context: 'Check your internet connection'
            },
            {
                pattern: /api.*key|authentication|unauthorized/i,
                message: 'API authentication error',
                context: 'Please check API configuration'
            },
            {
                pattern: /video.*not.*found|404/i,
                message: 'video not available',
                context: 'Video may be private or deleted'
            },
            {
                pattern: /quota.*exceeded|rate.*limit/i,
                message: 'API quota exceeded',
                context: 'Please try again later'
            },
            {
                pattern: /processing.*failed|summary.*generation.*error/i,
                message: 'processing error occurred',
                context: 'Try again or contact support'
            },
            {
                pattern: /storage.*error|notion.*error/i,
                message: 'storage operation failed',
                context: 'Check Notion integration'
            },
            {
                pattern: /server.*error|internal.*error/i,
                message: 'Server error',
                context: 'Please try again later'
            },
            {
                pattern: /TypeError|ReferenceError|SyntaxError|NetworkError/i,
                message: 'Application error occurred',
                context: 'Please refresh the page and try again'
            }
        ];

        // Find matching error pattern
        for (const mapping of errorMappings) {
            if (mapping.pattern.test(errorMessage)) {
                return mapping.message;
            }
        }

        // Fallback to shortened original message
        const shortMessage = errorMessage.length > 50 
            ? errorMessage.substring(0, 47) + '...'
            : errorMessage;
        
        return shortMessage;
    }

    /**
     * Get detailed error context for troubleshooting
     * @param {string|null} errorMessage - Raw error message from server
     * @returns {string} Troubleshooting context
     */
    getErrorContext(errorMessage) {
        if (!errorMessage) {
            return 'Unknown error occurred. Please try again.';
        }

        // Map common error patterns to troubleshooting context
        const errorMappings = [
            {
                pattern: /invalid.*url/i,
                context: 'Please ensure the URL is a valid YouTube link (youtube.com or youtu.be)'
            },
            {
                pattern: /network.*error|connection.*error|timeout/i,
                context: 'Check your internet connection and try again. If the problem persists, the server may be temporarily unavailable.'
            },
            {
                pattern: /api.*key|authentication|unauthorized/i,
                context: 'The API credentials may be invalid or expired. Please contact an administrator.'
            },
            {
                pattern: /video.*not.*found|404/i,
                context: 'The video may be private, deleted, or the URL may be incorrect. Please verify the video is publicly accessible.'
            },
            {
                pattern: /quota.*exceeded|rate.*limit/i,
                context: 'The API usage limit has been reached. Please wait a few minutes before trying again.'
            },
            {
                pattern: /processing.*failed|summary.*generation.*error/i,
                context: 'The AI service encountered an error while processing the video. This may be due to video content or temporary service issues.'
            },
            {
                pattern: /storage.*error|notion.*error/i,
                context: 'Failed to save the summary to Notion. Please check the Notion integration settings and permissions.'
            },
            {
                pattern: /server.*error|internal.*error/i,
                context: 'An internal server error occurred. Please try again in a few minutes.'
            }
        ];

        // Find matching error pattern
        for (const mapping of errorMappings) {
            if (mapping.pattern.test(errorMessage)) {
                return mapping.context;
            }
        }

        // Fallback context
        return 'An unexpected error occurred. Please try again or contact support if the problem persists.';
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
     * Create action buttons for completed and failed items
     * @param {Object} item - Queue item
     * @returns {HTMLElement|null}
     */
    createActionButtons(item) {
        const buttons = [];
        
        // Handle completed items
        if (item.status === 'completed') {
            // Main chat log button - always show for completed items
            const viewLogBtn = this.createViewLogButton(item);
            buttons.push(viewLogBtn);
            
            // Chunk log buttons for chunked videos
            if (item.chunk_logs && item.chunk_logs.length > 0) {
                item.chunk_logs.forEach((log, index) => {
                    const chunkBtn = this.createChunkLogButton(item, index);
                    buttons.push(chunkBtn);
                });
            }
        }
        
        // Handle failed items
        if (item.status === 'failed') {
            // Retry button for failed items
            const retryBtn = this.createRetryButton(item);
            buttons.push(retryBtn);
            
            // View error details button
            const errorBtn = this.createErrorDetailsButton(item);
            buttons.push(errorBtn);
            
            // View log button if chat log exists
            if (item.chat_log_path) {
                const viewLogBtn = this.createViewLogButton(item);
                buttons.push(viewLogBtn);
            }
        }
        
        if (buttons.length === 0) return null;
        
        const actionsContainer = DOMUtils.createElement('div', { className: 'item-actions' });
        buttons.forEach(button => actionsContainer.appendChild(button));
        
        return actionsContainer;
    }

    /**
     * Create view log button
     * @param {Object} item - Queue item
     * @returns {HTMLElement}
     */
    createViewLogButton(item) {
        const viewLogBtn = DOMUtils.createElement('button', {
            className: 'action-btn eye-btn primary',
            title: 'View processing log'
        });
        
        const eyeIcon = DOMUtils.createElement('span', { className: 'eye-icon' }, '👁');
        const btnText = DOMUtils.createElement('span', { className: 'btn-text' }, 'View Log');
        
        viewLogBtn.appendChild(eyeIcon);
        viewLogBtn.appendChild(btnText);
        
        DOMUtils.addEventListener(viewLogBtn, 'click', (e) => {
            e.stopPropagation();
            window.app.showChatLog(item.id);
        });
        
        return viewLogBtn;
    }

    /**
     * Create chunk log button
     * @param {Object} item - Queue item
     * @param {number} index - Chunk index
     * @returns {HTMLElement}
     */
    createChunkLogButton(item, index) {
        const chunkBtn = DOMUtils.createElement('button', {
            className: 'action-btn eye-btn chunk-btn',
            title: `View chunk ${index + 1} log`
        });
        
        const chunkEyeIcon = DOMUtils.createElement('span', { className: 'eye-icon' }, '👁');
        const chunkNumber = DOMUtils.createElement('span', { className: 'chunk-number' }, (index + 1).toString());
        
        chunkBtn.appendChild(chunkEyeIcon);
        chunkBtn.appendChild(chunkNumber);
        
        DOMUtils.addEventListener(chunkBtn, 'click', (e) => {
            e.stopPropagation();
            window.app.showChatLog(item.id, index);
        });
        
        return chunkBtn;
    }

    /**
     * Create retry button for failed items
     * @param {Object} item - Queue item
     * @returns {HTMLElement}
     */
    createRetryButton(item) {
        const retryBtn = DOMUtils.createElement('button', {
            className: 'action-btn retry-btn',
            title: 'Retry processing this item'
        });
        
        const retryIcon = DOMUtils.createElement('span', { className: 'retry-icon' }, '🔄');
        const btnText = DOMUtils.createElement('span', { className: 'btn-text' }, 'Retry');
        
        retryBtn.appendChild(retryIcon);
        retryBtn.appendChild(btnText);
        
        DOMUtils.addEventListener(retryBtn, 'click', async (e) => {
            e.stopPropagation();
            await this.handleRetry(item);
        });
        
        return retryBtn;
    }

    /**
     * Create error details button for failed items
     * @param {Object} item - Queue item
     * @returns {HTMLElement}
     */
    createErrorDetailsButton(item) {
        const errorBtn = DOMUtils.createElement('button', {
            className: 'action-btn error-btn',
            title: 'View error details and troubleshooting'
        });
        
        const errorIcon = DOMUtils.createElement('span', { className: 'error-icon' }, '⚠️');
        const btnText = DOMUtils.createElement('span', { className: 'btn-text' }, 'Details');
        
        errorBtn.appendChild(errorIcon);
        errorBtn.appendChild(btnText);
        
        DOMUtils.addEventListener(errorBtn, 'click', (e) => {
            e.stopPropagation();
            this.showErrorDetails(item);
        });
        
        return errorBtn;
    }

    /**
     * Handle retry functionality for failed items
     * @param {Object} item - Failed queue item
     */
    async handleRetry(item) {
        try {
            // Show loading state
            const retryBtn = document.querySelector(`[data-item-id="${item.id}"] .retry-btn`);
            if (retryBtn) {
                retryBtn.disabled = true;
                retryBtn.innerHTML = '<span class="retry-icon spinning">🔄</span><span class="btn-text">Retrying...</span>';
            }

            // Call retry endpoint
            const response = await fetch(`/api/retry/${item.id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to retry item');
            }
            
            // Show success feedback
            this.showRetryFeedback(item.id, 'success', 'Item added back to queue');
            
        } catch (error) {
            console.error('Retry failed:', error);
            
            // Show error feedback
            this.showRetryFeedback(item.id, 'error', error.message || 'Failed to retry item');
            
            // Reset button state
            const retryBtn = document.querySelector(`[data-item-id="${item.id}"] .retry-btn`);
            if (retryBtn) {
                retryBtn.disabled = false;
                retryBtn.innerHTML = '<span class="retry-icon">🔄</span><span class="btn-text">Retry</span>';
            }
        }
    }

    /**
     * Show retry feedback to user
     * @param {string} itemId - Item ID
     * @param {string} type - 'success' or 'error'
     * @param {string} message - Feedback message
     */
    showRetryFeedback(itemId, type, message) {
        const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
        if (!itemElement) return;

        // Create feedback element
        const feedback = DOMUtils.createElement('div', {
            className: `retry-feedback ${type}`
        }, message);

        // Add to item
        itemElement.appendChild(feedback);

        // Remove after 3 seconds
        setTimeout(() => {
            if (feedback.parentNode) {
                feedback.parentNode.removeChild(feedback);
            }
        }, 3000);
    }

    /**
     * Show detailed error information in a modal
     * @param {Object} item - Failed queue item
     */
    showErrorDetails(item) {
        const errorMessage = item.error_message || 'Unknown error';
        const errorContext = this.getErrorContext(errorMessage);
        
        // Create error details modal content
        const modalContent = `
            <div class="error-details-modal">
                <div class="error-summary">
                    <h4>Processing Failed</h4>
                    <p class="error-message">${this.getErrorDisplayText(errorMessage)}</p>
                </div>
                
                <div class="error-context">
                    <h5>What happened?</h5>
                    <p>${errorContext}</p>
                </div>
                
                <div class="error-actions">
                    <h5>What can you do?</h5>
                    <ul>
                        <li>Click "Retry" to try processing again</li>
                        <li>Check that the YouTube URL is valid and publicly accessible</li>
                        <li>Verify your internet connection is stable</li>
                        <li>Try again in a few minutes if it's a temporary service issue</li>
                    </ul>
                </div>
                
                <div class="error-technical">
                    <details>
                        <summary>Technical Details</summary>
                        <pre class="error-raw">${errorMessage}</pre>
                    </details>
                </div>
            </div>
        `;

        // Show in a modal (reuse chat log modal structure)
        this.showCustomModal('Error Details', modalContent);
    }

    /**
     * Show custom modal with content
     * @param {string} title - Modal title
     * @param {string} content - HTML content
     */
    showCustomModal(title, content) {
        const modal = DOMUtils.getElementById('chat-modal-overlay');
        const modalTitle = DOMUtils.getElementById('chat-modal-title');
        const modalContent = DOMUtils.getElementById('chat-log-content');
        
        if (modal && modalTitle && modalContent) {
            modalTitle.textContent = title;
            modalContent.innerHTML = content;
            modal.classList.add('active');
        }
    }

    /**
     * Create error details section for failed items
     * @param {Object} item - Failed queue item
     * @returns {HTMLElement|null}
     */
    createErrorDetails(item) {
        if (!item.error_message) return null;

        const errorDetails = DOMUtils.createElement('div', { className: 'error-details' });
        
        const errorText = DOMUtils.createElement('div', { 
            className: 'error-text' 
        }, this.getErrorDisplayText(item.error_message));
        
        const errorHint = DOMUtils.createElement('div', { 
            className: 'error-hint' 
        }, 'Click "Details" for troubleshooting help');
        
        errorDetails.appendChild(errorText);
        errorDetails.appendChild(errorHint);
        
        return errorDetails;
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