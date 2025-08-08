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
     * Add URL to queue (placeholder for task 8)
     * @param {string} url - YouTube URL
     * @param {string|null} customPrompt - Custom prompt
     */
    async addQueueItem(url, customPrompt = null) {
        console.log('addQueueItem called - to be implemented in task 8', { url, customPrompt });
        // TODO: Implement URL validation and API call in task 8
        throw new Error('URL submission functionality will be implemented in task 8');
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