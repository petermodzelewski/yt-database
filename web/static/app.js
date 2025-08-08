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
        
        // Setup main event listeners
        this.setupEventListeners();
        
        // Initial render
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
            
            const response = await fetch('/api/queue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            if (!result.success) {
                throw new Error(result.error || 'Failed to add URL to queue');
            }
            
            console.log('URL added successfully:', result);
            
            // Refresh queue display after successful addition
            // This will be implemented in task 9 with real-time updates
            // For now, we could manually refresh the queue status
            
            return result;
            
        } catch (error) {
            console.error('Failed to add URL to queue:', error);
            throw error;
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
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new YouTubeNotionApp();
});

// Export for testing purposes
if (typeof module !== 'undefined' && module.exports) {
    module.exports = YouTubeNotionApp;
}

// Make available globally for browser
if (typeof window !== 'undefined') {
    window.YouTubeNotionApp = YouTubeNotionApp;
}