/**
 * Chat Log Modal Component
 * 
 * Component for displaying chat logs in a modal
 */

class ChatLogModal {
    constructor() {
        this.modal = DOMUtils.getElementById('chat-modal-overlay');
        this.title = DOMUtils.getElementById('chat-modal-title');
        this.content = DOMUtils.getElementById('chat-log-content');
        this.closeButton = DOMUtils.getElementById('chat-modal-close-btn');
        
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Close button
        if (this.closeButton) {
            DOMUtils.addEventListener(this.closeButton, 'click', () => {
                this.hide();
            });
        }

        // Modal overlay click to close
        if (this.modal) {
            DOMUtils.addEventListener(this.modal, 'click', (e) => {
                if (e.target === this.modal) {
                    this.hide();
                }
            });
        }

        // Escape key to close
        DOMUtils.addEventListener(document, 'keydown', (e) => {
            if (e.key === 'Escape' && this.modal?.classList.contains('active')) {
                this.hide();
            }
        });
    }

    /**
     * Show chat log modal with content
     * @param {string} itemId - Queue item ID
     * @param {number|null} chunkIndex - Chunk index for chunked videos
     */
    async show(itemId, chunkIndex = null) {
        if (!this.modal) return;

        // Set title
        const titleText = chunkIndex !== null ? 
            `Processing Log - Chunk ${chunkIndex + 1}` : 
            'Processing Log';
        
        if (this.title) {
            this.title.textContent = titleText;
        }

        // Show modal
        this.modal.classList.add('active');

        // Load content
        await this.loadChatLog(itemId, chunkIndex);
    }

    /**
     * Hide the chat log modal
     */
    hide() {
        if (this.modal) {
            this.modal.classList.remove('active');
        }
    }

    /**
     * Load chat log content from API
     * @param {string} itemId - Queue item ID
     * @param {number|null} chunkIndex - Chunk index
     */
    async loadChatLog(itemId, chunkIndex = null) {
        if (!this.content) return;

        // Show loading state
        this.content.innerHTML = 'Loading chat log...';

        try {
            const url = chunkIndex !== null ? 
                `/api/chat-log/${itemId}?chunk=${chunkIndex}` : 
                `/api/chat-log/${itemId}`;
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.content) {
                this.content.textContent = data.content;
            } else {
                this.content.textContent = 'No chat log available for this item.';
            }
        } catch (error) {
            console.error('Failed to load chat log:', error);
            this.content.textContent = `Error loading chat log: ${error.message}`;
        }
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatLogModal;
}

// Make available globally
window.ChatLogModal = ChatLogModal;