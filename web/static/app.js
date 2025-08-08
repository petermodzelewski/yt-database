/**
 * YouTube to Notion Queue Manager - Frontend Application
 * 
 * This file provides the basic structure for the web UI application.
 * It includes placeholder functions and event handlers that will be
 * implemented in subsequent tasks.
 */

class YouTubeNotionApp {
    constructor() {
        this.init();
    }

    init() {
        console.log('YouTube to Notion Queue Manager initialized');
        this.setupEventListeners();
        this.updateStats();
    }

    setupEventListeners() {
        // Add URL button
        const addUrlBtn = document.getElementById('add-url-btn');
        if (addUrlBtn) {
            addUrlBtn.addEventListener('click', () => {
                console.log('Add URL button clicked - functionality to be implemented');
                // TODO: Implement in task 8
            });
        }

        // Modal close buttons
        const modalCloseButtons = document.querySelectorAll('.modal-close');
        modalCloseButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const modal = e.target.closest('.modal-overlay');
                if (modal) {
                    modal.classList.remove('active');
                }
            });
        });

        // Close modal on overlay click
        const modalOverlays = document.querySelectorAll('.modal-overlay');
        modalOverlays.forEach(overlay => {
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) {
                    overlay.classList.remove('active');
                }
            });
        });
    }

    updateStats() {
        // Update header statistics
        const totalCount = document.getElementById('total-count');
        const processingCount = document.getElementById('processing-count');
        const todoCount = document.getElementById('todo-count');
        const inProgressCount = document.getElementById('in-progress-count');
        const doneCount = document.getElementById('done-count');

        // Placeholder values - will be updated with real data in later tasks
        if (totalCount) totalCount.textContent = '0';
        if (processingCount) processingCount.textContent = '0';
        if (todoCount) todoCount.textContent = '0';
        if (inProgressCount) inProgressCount.textContent = '0';
        if (doneCount) doneCount.textContent = '0';
    }

    // Placeholder methods for future implementation
    addQueueItem(url, customPrompt = null) {
        console.log('addQueueItem called - to be implemented in task 8');
        // TODO: Implement URL validation and API call
    }

    updateQueueDisplay(queueData) {
        console.log('updateQueueDisplay called - to be implemented in task 9');
        // TODO: Implement real-time UI updates
    }

    showChatLog(itemId) {
        console.log('showChatLog called - to be implemented in task 11');
        // TODO: Implement chat log modal
    }

    // Utility method to create queue item HTML
    createQueueItemHTML(item) {
        return `
            <div class="queue-item" data-item-id="${item.id}">
                <div class="item-header">
                    <div class="item-thumbnail">
                        ${item.thumbnail_url ? 
                            `<img src="${item.thumbnail_url}" alt="Video thumbnail">` : 
                            'No thumbnail'
                        }
                    </div>
                    <div class="item-info">
                        <div class="item-title">${item.title || 'Loading...'}</div>
                        <div class="item-channel">${item.channel || ''}</div>
                        <div class="item-duration">${item.duration || ''}</div>
                    </div>
                </div>
                <div class="item-status">
                    <span class="status-text">
                        <span class="status-icon ${item.status}"></span>
                        ${this.getStatusText(item)}
                    </span>
                </div>
                ${item.status === 'in_progress' ? this.createProgressBar(item) : ''}
                ${item.status === 'completed' ? this.createActionButtons(item) : ''}
            </div>
        `;
    }

    getStatusText(item) {
        switch (item.status) {
            case 'todo':
                return 'Waiting in queue';
            case 'in_progress':
                return item.current_phase || 'Processing...';
            case 'completed':
                return 'Completed successfully';
            case 'failed':
                return item.error_message || 'Processing failed';
            default:
                return 'Unknown status';
        }
    }

    createProgressBar(item) {
        const progress = this.calculateProgress(item);
        return `
            <div class="progress-bar">
                <div class="progress-fill" style="width: ${progress}%"></div>
            </div>
        `;
    }

    calculateProgress(item) {
        // Simple progress calculation based on current phase
        const phases = ['metadata', 'summary', 'upload'];
        const currentPhase = item.current_phase || '';
        
        if (currentPhase.includes('metadata')) return 25;
        if (currentPhase.includes('summary')) return 50;
        if (currentPhase.includes('upload')) return 75;
        return 10; // Default progress
    }

    createActionButtons(item) {
        let buttons = '';
        
        if (item.chat_log_path) {
            buttons += `<button class="action-btn primary" onclick="app.showChatLog('${item.id}')">👁 View Log</button>`;
        }
        
        if (item.chunk_logs && item.chunk_logs.length > 0) {
            item.chunk_logs.forEach((log, index) => {
                buttons += `<button class="action-btn" onclick="app.showChatLog('${item.id}', ${index})">👁 ${index + 1}</button>`;
            });
        }
        
        return buttons ? `<div class="item-actions">${buttons}</div>` : '';
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new YouTubeNotionApp();
});

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = YouTubeNotionApp;
}