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
        this.content.innerHTML = '<div class="loading-spinner">Loading chat log...</div>';

        try {
            const url = chunkIndex !== null ? 
                `/api/chat-log/${itemId}?chunk=${chunkIndex}` : 
                `/api/chat-log/${itemId}`;
            
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            
            if (data.chat_log) {
                // Format and display the chat log with proper styling
                this.displayChatLog(data.chat_log, data);
            } else {
                this.content.innerHTML = '<div class="no-content">No chat log available for this item.</div>';
            }
        } catch (error) {
            console.error('Failed to load chat log:', error);
            this.content.innerHTML = `<div class="error-message">Error loading chat log: ${error.message}</div>`;
        }
    }

    /**
     * Display formatted chat log content
     * @param {string} chatLog - Raw chat log content
     * @param {Object} metadata - Additional metadata about the item
     */
    displayChatLog(chatLog, metadata) {
        if (!this.content) return;

        // Create container for formatted content
        const container = DOMUtils.createElement('div', { className: 'chat-log-container' });

        // Add metadata header if available
        if (metadata.title || metadata.url) {
            const header = DOMUtils.createElement('div', { className: 'chat-log-header' });
            
            if (metadata.title) {
                const title = DOMUtils.createElement('h4', { className: 'chat-log-title' }, metadata.title);
                header.appendChild(title);
            }
            
            if (metadata.url) {
                const url = DOMUtils.createElement('a', { 
                    className: 'chat-log-url',
                    href: metadata.url,
                    target: '_blank',
                    rel: 'noopener noreferrer'
                }, metadata.url);
                header.appendChild(url);
            }
            
            if (metadata.completed_at) {
                const timestamp = DOMUtils.createElement('div', { 
                    className: 'chat-log-timestamp' 
                }, `Completed: ${new Date(metadata.completed_at).toLocaleString()}`);
                header.appendChild(timestamp);
            }
            
            container.appendChild(header);
        }

        // Format and display the chat log content
        const content = DOMUtils.createElement('div', { className: 'chat-log-text' });
        
        // Apply syntax highlighting and formatting
        const formattedContent = this.formatChatLogContent(chatLog);
        content.innerHTML = formattedContent;
        
        container.appendChild(content);
        
        // Clear and set new content
        this.content.innerHTML = '';
        this.content.appendChild(container);
    }

    /**
     * Format chat log content with syntax highlighting and proper styling
     * @param {string} content - Raw chat log content
     * @returns {string} Formatted HTML content
     */
    formatChatLogContent(content) {
        if (!content) return '<div class="no-content">No content available</div>';

        // Escape HTML to prevent XSS
        const escaped = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');

        // Apply formatting for common patterns
        let formatted = escaped
            // Highlight timestamps [HH:MM:SS] or [MM:SS]
            .replace(/\[(\d{1,2}:\d{2}(?::\d{2})?)\]/g, '<span class="timestamp">[$1]</span>')
            // Highlight user/assistant labels
            .replace(/^(User|Assistant|Human|AI):/gm, '<span class="speaker">$1:</span>')
            // Highlight section headers (lines starting with ##)
            .replace(/^(#{1,3})\s*(.+)$/gm, '<span class="header">$1 $2</span>')
            // Highlight URLs
            .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="chat-url">$1</a>')
            // Highlight code blocks (simple detection)
            .replace(/```([\s\S]*?)```/g, '<pre class="code-block">$1</pre>')
            // Highlight inline code
            .replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
            // Preserve line breaks
            .replace(/\n/g, '<br>');

        return formatted;
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ChatLogModal;
}

// Make available globally
window.ChatLogModal = ChatLogModal;