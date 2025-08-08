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
            this.hide();
        } catch (error) {
            this.showError(error.message || 'Failed to add URL to queue');
            this.setLoading(false);
        }
    }

    /**
     * Validate YouTube URL format
     * @param {string} url - URL to validate
     * @returns {boolean}
     */
    validateUrl(url) {
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/)[a-zA-Z0-9_-]{11}/;
        return youtubeRegex.test(url);
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
            this.errorElement.classList.remove('active');
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
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = UrlInput;
}

// Make available globally
window.UrlInput = UrlInput;