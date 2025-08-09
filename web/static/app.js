/**
 * YouTube to Notion Queue Manager - Frontend Application
 * 
 * Main application class with component-based architecture.
 * Coordinates between components and manages application state.
 */

/**
 * Main application class with component-based architecture
 */
class YouTubeNotionApp {
    constructor() {
        this.components = {};
        this.init();
    }

    init() {
        console.log('YouTube to Notion Queue Manager initialized');
        
        // Initialize components
        this.components.queueColumns = new QueueColumns();
        this.components.urlInput = new UrlInput();
        this.components.chatLogModal = new ChatLogModal();
        this.components.sseConnection = new SSEConnection(this);
        
        // Setup main event listeners
        this.setupEventListeners();
        
        // Initial render (will be updated by SSE connection)
        this.updateQueueDisplay({ todo: [], 'in-progress': [], done: [] });
    }

    setupEventListeners() {
        // Add URL button
        const addUrlBtn = DOMUtils.getElementById('add-url-btn');
        if (addUrlBtn) {
            DOMUtils.addEventListener(addUrlBtn, 'click', () => {
                this.components.urlInput.show();
            });
        }
    }

    /**
     * Add URL to queue with API call
     * @param {string} url - YouTube URL
     * @param {string|null} customPrompt - Custom prompt
     */
    async addQueueItem(url, customPrompt = null) {
        console.log('Adding URL to queue:', { url, customPrompt });
        
        try {
            const requestBody = {
                url: url
            };
            
            // Add custom prompt if provided
            if (customPrompt) {
                requestBody.custom_prompt = customPrompt;
            }

            // Create AbortController for timeout handling
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout
            
            const response = await fetch('/api/queue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                let errorData = {};
                try {
                    errorData = await response.json();
                } catch (parseError) {
                    console.warn('Failed to parse error response:', parseError);
                }
                
                // Create descriptive error message based on status code
                let errorMessage = errorData.error || this.getHttpErrorMessage(response.status);
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to add URL to queue');
            }
            
            console.log('URL added successfully:', result);
            
            // SSE connection will automatically update the UI
            // No need to manually refresh queue status
            
            return result;
            
        } catch (error) {
            console.error('Failed to add URL to queue:', error);
            
            // Enhance error with network-specific information
            if (error.name === 'AbortError') {
                throw new Error('Request timed out - please try again');
            } else if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error('Network error - please check your internet connection');
            }
            
            throw error;
        }
    }

    /**
     * Get user-friendly HTTP error message
     * @param {number} status - HTTP status code
     * @returns {string} Error message
     */
    getHttpErrorMessage(status) {
        switch (status) {
            case 400:
                return 'Invalid request - please check the URL format';
            case 401:
                return 'Authentication error - please refresh the page';
            case 403:
                return 'Access denied - insufficient permissions';
            case 404:
                return 'Service not found - please refresh the page';
            case 429:
                return 'Too many requests - please wait a moment';
            case 500:
                return 'Server error - please try again later';
            case 502:
                return 'Service temporarily unavailable';
            case 503:
                return 'Service maintenance - please try again later';
            case 504:
                return 'Request timeout - please try again';
            default:
                return `Server error (${status}) - please try again`;
        }
    }

    /**
     * Update queue display with new data
     * @param {Object} queueData - Queue data organized by status
     */
    updateQueueDisplay(queueData) {
        console.log('updateQueueDisplay called', queueData);
        this.components.queueColumns.render(queueData);
    }

    /**
     * Show chat log modal
     * @param {string} itemId - Queue item ID
     * @param {number|null} chunkIndex - Chunk index for chunked videos
     */
    showChatLog(itemId, chunkIndex = null) {
        console.log('showChatLog called', { itemId, chunkIndex });
        this.components.chatLogModal.show(itemId, chunkIndex);
    }

    /**
     * Get reference to a component
     * @param {string} name - Component name
     * @returns {Object|null}
     */
    getComponent(name) {
        return this.components[name] || null;
    }

    /**
     * Get connection status from SSE component
     * @returns {Object} Connection statistics
     */
    getConnectionStatus() {
        return this.components.sseConnection ? this.components.sseConnection.getStats() : null;
    }

    /**
     * Manually trigger reconnection
     */
    reconnect() {
        if (this.components.sseConnection) {
            this.components.sseConnection.reconnect();
        }
    }

    /**
     * Cleanup when app is destroyed
     */
    destroy() {
        console.log('YouTube to Notion App: Cleaning up');
        
        // Cleanup all components
        Object.values(this.components).forEach(component => {
            if (component && typeof component.destroy === 'function') {
                component.destroy();
            }
        });
        
        this.components = {};
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new YouTubeNotionApp();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.app && typeof window.app.destroy === 'function') {
        window.app.destroy();
    }
});

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = YouTubeNotionApp;
}

// Make available globally for browser
if (typeof window !== 'undefined') {
    window.YouTubeNotionApp = YouTubeNotionApp;
}