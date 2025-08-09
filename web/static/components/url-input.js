/**
 * URL Input Component
 * 
 * Component for handling URL input popup functionality
 */

class UrlInput {
    constructor() {
        this.modal = DOMUtils.getElementById('url-modal-overlay');
        this.form = DOMUtils.getElementById('url-form');
        this.urlInput = DOMUtils.getElementById('youtube-url');
        this.customPromptInput = DOMUtils.getElementById('custom-prompt');
        this.errorElement = DOMUtils.getElementById('url-error');
        this.submitButton = DOMUtils.getElementById('submit-btn');
        this.cancelButton = DOMUtils.getElementById('cancel-btn');
        this.closeButton = DOMUtils.getElementById('modal-close-btn');
        
        this.init();
    }

    init() {
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Form submission
        if (this.form) {
            DOMUtils.addEventListener(this.form, 'submit', (e) => {
                e.preventDefault();
                this.handleSubmit();
            });
        }

        // Cancel button
        if (this.cancelButton) {
            DOMUtils.addEventListener(this.cancelButton, 'click', () => {
                this.hide();
            });
        }

        // Close button
        if (this.closeButton) {
            DOMUtils.addEventListener(this.closeButton, 'click', () => {
                this.hide();
            });
        }

        // URL input validation
        if (this.urlInput) {
            DOMUtils.addEventListener(this.urlInput, 'input', () => {
                this.clearError();
                this.validateInputRealTime();
            });
            
            DOMUtils.addEventListener(this.urlInput, 'paste', () => {
                // Clear error and validate after paste
                setTimeout(() => {
                    this.clearError();
                    this.validateInputRealTime();
                }, 10);
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

        // Keyboard shortcuts
        DOMUtils.addEventListener(document, 'keydown', (e) => {
            if (this.modal && this.modal.classList.contains('active')) {
                if (e.key === 'Escape') {
                    this.hide();
                } else if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    // Ctrl+Enter or Cmd+Enter to submit
                    e.preventDefault();
                    this.handleSubmit();
                }
            }
        });
    }

    /**
     * Show the URL input modal
     */
    show() {
        if (this.modal) {
            this.modal.classList.add('active');
            if (this.urlInput) {
                this.urlInput.focus();
            }
        }
    }

    /**
     * Hide the URL input modal
     */
    hide() {
        if (this.modal) {
            this.modal.classList.remove('active');
            this.reset();
        }
    }

    /**
     * Reset form to initial state
     */
    reset() {
        if (this.form) {
            this.form.reset();
        }
        this.clearError();
        this.setLoading(false);
    }

    /**
     * Handle form submission
     */
    async handleSubmit() {
        const url = this.urlInput?.value.trim();
        const customPrompt = this.customPromptInput?.value.trim() || null;

        if (!url) {
            this.showError('Please enter a YouTube URL');
            return;
        }

        if (!this.validateUrl(url)) {
            this.showError('Please enter a valid YouTube URL');
            return;
        }

        this.setLoading(true);

        try {
            // Call the main app's addQueueItem method
            await window.app.addQueueItem(url, customPrompt);
            this.showSuccess('URL added to queue successfully!');
            
            // Hide modal after short delay to show success message
            setTimeout(() => {
                this.hide();
            }, 1000);
            
        } catch (error) {
            console.error('Failed to add URL:', error);
            this.showError(this.getErrorMessage(error));
            this.setLoading(false);
        }
    }

    /**
     * Get user-friendly error message from error object
     * @param {Error|Object} error - Error object or response
     * @returns {string} User-friendly error message
     */
    getErrorMessage(error) {
        // Handle network errors
        if (error.name === 'TypeError' && error.message.includes('fetch')) {
            return 'Network error - please check your internet connection';
        }

        // Handle timeout errors
        if (error.name === 'AbortError' || error.message.includes('timeout')) {
            return 'Request timed out - please try again';
        }

        // Handle server errors
        if (error.message.includes('HTTP 5')) {
            return 'Server error - please try again later';
        }

        // Handle API errors
        if (error.message.includes('HTTP 4')) {
            return 'Invalid request - please check the URL format';
        }

        // Handle specific error messages
        const message = error.message || 'Unknown error';
        
        if (message.includes('invalid') && message.includes('url')) {
            return 'Please enter a valid YouTube URL';
        }
        
        if (message.includes('queue') && message.includes('full')) {
            return 'Queue is full - please wait for some items to complete';
        }

        if (message.includes('network') || message.includes('connection')) {
            return 'Network connection error - please check your internet';
        }

        // Return original message if it's already user-friendly
        if (message.length < 100 && !message.includes('Error:') && !message.includes('Exception:')) {
            return message;
        }

        // Fallback for technical errors
        return 'Failed to add URL to queue - please try again';
    }

    /**
     * Show success message
     * @param {string} message - Success message
     */
    showSuccess(message) {
        if (this.errorElement) {
            this.errorElement.textContent = message;
            this.errorElement.classList.remove('active');
            this.errorElement.classList.add('success', 'active');
        }
    }

    /**
     * Validate YouTube URL format using comprehensive regex patterns
     * @param {string} url - URL to validate
     * @returns {boolean}
     */
    validateUrl(url) {
        // Comprehensive YouTube URL patterns
        const youtubePatterns = [
            // Standard watch URLs
            /^https?:\/\/(www\.)?youtube\.com\/watch\?v=[a-zA-Z0-9_-]{11}(&.*)?$/,
            // Short URLs
            /^https?:\/\/youtu\.be\/[a-zA-Z0-9_-]{11}(\?.*)?$/,
            // Embed URLs
            /^https?:\/\/(www\.)?youtube\.com\/embed\/[a-zA-Z0-9_-]{11}(\?.*)?$/,
            // Mobile URLs
            /^https?:\/\/m\.youtube\.com\/watch\?v=[a-zA-Z0-9_-]{11}(&.*)?$/,
            // YouTube Music URLs
            /^https?:\/\/music\.youtube\.com\/watch\?v=[a-zA-Z0-9_-]{11}(&.*)?$/
        ];
        
        return youtubePatterns.some(pattern => pattern.test(url));
    }

    /**
     * Show error message
     * @param {string} message - Error message
     */
    showError(message) {
        if (this.errorElement) {
            this.errorElement.textContent = message;
            this.errorElement.classList.add('active');
        }
    }

    /**
     * Clear error message
     */
    clearError() {
        if (this.errorElement) {
            this.errorElement.textContent = '';
            this.errorElement.classList.remove('active', 'success');
        }
    }

    /**
     * Set loading state
     * @param {boolean} loading - Loading state
     */
    setLoading(loading) {
        if (this.submitButton) {
            const btnText = this.submitButton.querySelector('.btn-text');
            const btnSpinner = this.submitButton.querySelector('.btn-spinner');
            
            if (loading) {
                this.submitButton.disabled = true;
                if (btnText) btnText.style.display = 'none';
                if (btnSpinner) btnSpinner.style.display = 'inline';
            } else {
                this.submitButton.disabled = false;
                if (btnText) btnText.style.display = 'inline';
                if (btnSpinner) btnSpinner.style.display = 'none';
            }
        }
    }

    /**
     * Validate input in real-time and provide visual feedback
     */
    validateInputRealTime() {
        if (!this.urlInput) return;
        
        const url = this.urlInput.value.trim();
        
        if (url && !this.validateUrl(url)) {
            this.urlInput.style.borderColor = '#d32f2f';
        } else {
            this.urlInput.style.borderColor = '';
        }
    }

    /**
     * Extract video ID from YouTube URL for additional validation
     * @param {string} url - YouTube URL
     * @returns {string|null} - Video ID or null if not found
     */
    extractVideoId(url) {
        const patterns = [
            /(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})/,
            /youtube\.com\/v\/([a-zA-Z0-9_-]{11})/,
            /music\.youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})/
        ];
        
        for (const pattern of patterns) {
            const match = url.match(pattern);
            if (match) {
                return match[1];
            }
        }
        
        return null;
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UrlInput;
}

// Make available globally for browser
if (typeof window !== 'undefined') {
    window.UrlInput = UrlInput;
}