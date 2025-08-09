/**
 * Unit tests for URL Input Component
 * 
 * Tests URL validation, form handling, and error display functionality
 */

// Mock DOM utilities for testing
class MockDOMUtils {
    static getElementById(id) {
        return document.getElementById(id);
    }
    
    static addEventListener(element, event, handler, options = {}) {
        if (element && element.addEventListener) {
            element.addEventListener(event, handler, options);
        }
    }
    
    static createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'dataset') {
                Object.entries(value).forEach(([dataKey, dataValue]) => {
                    element.dataset[dataKey] = dataValue;
                });
            } else {
                element.setAttribute(key, value);
            }
        });
        
        if (typeof content === 'string') {
            element.innerHTML = content;
        }
        
        return element;
    }
}

// Mock global DOMUtils
global.DOMUtils = MockDOMUtils;

// Mock DOM elements
function createMockDOM() {
    document.body.innerHTML = `
        <div class="modal-overlay" id="url-modal-overlay">
            <div class="modal-content">
                <form class="url-form" id="url-form">
                    <input type="url" id="youtube-url" name="url" />
                    <textarea id="custom-prompt" name="customPrompt"></textarea>
                    <div class="form-error" id="url-error"></div>
                    <button type="submit" id="submit-btn">
                        <span class="btn-text">Add to Queue</span>
                        <span class="btn-spinner" style="display: none;">⟳</span>
                    </button>
                    <button type="button" id="cancel-btn">Cancel</button>
                </form>
                <button class="modal-close" id="modal-close-btn">&times;</button>
            </div>
        </div>
    `;
}

// Mock window.app
global.window = {
    app: {
        addQueueItem: jest.fn()
    }
};

describe('UrlInput Component', () => {
    let urlInput;
    
    beforeEach(() => {
        createMockDOM();
        
        // Reset window.app mock
        global.window.app = {
            addQueueItem: jest.fn()
        };
        
        // Load the UrlInput component
        const UrlInput = require('../components/url-input.js');
        urlInput = new UrlInput();
    });
    
    afterEach(() => {
        jest.clearAllMocks();
        document.body.innerHTML = '';
    });
    
    describe('URL Validation', () => {
        test('should validate standard YouTube watch URLs', () => {
            const validUrls = [
                'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'http://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'https://youtube.com/watch?v=dQw4w9WgXcQ',
                'https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s',
                'https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLrAXtmRdnEQy8VJqQzNYaYzOzHjzLQiEP'
            ];
            
            validUrls.forEach(url => {
                expect(urlInput.validateUrl(url)).toBe(true);
            });
        });
        
        test('should validate YouTube short URLs', () => {
            const validUrls = [
                'https://youtu.be/dQw4w9WgXcQ',
                'http://youtu.be/dQw4w9WgXcQ',
                'https://youtu.be/dQw4w9WgXcQ?t=30',
                'https://youtu.be/dQw4w9WgXcQ?si=abc123'
            ];
            
            validUrls.forEach(url => {
                expect(urlInput.validateUrl(url)).toBe(true);
            });
        });
        
        test('should validate YouTube embed URLs', () => {
            const validUrls = [
                'https://www.youtube.com/embed/dQw4w9WgXcQ',
                'http://www.youtube.com/embed/dQw4w9WgXcQ',
                'https://youtube.com/embed/dQw4w9WgXcQ',
                'https://www.youtube.com/embed/dQw4w9WgXcQ?start=30'
            ];
            
            validUrls.forEach(url => {
                expect(urlInput.validateUrl(url)).toBe(true);
            });
        });
        
        test('should validate mobile YouTube URLs', () => {
            const validUrls = [
                'https://m.youtube.com/watch?v=dQw4w9WgXcQ',
                'http://m.youtube.com/watch?v=dQw4w9WgXcQ',
                'https://m.youtube.com/watch?v=dQw4w9WgXcQ&t=30s'
            ];
            
            validUrls.forEach(url => {
                expect(urlInput.validateUrl(url)).toBe(true);
            });
        });
        
        test('should validate YouTube Music URLs', () => {
            const validUrls = [
                'https://music.youtube.com/watch?v=dQw4w9WgXcQ',
                'http://music.youtube.com/watch?v=dQw4w9WgXcQ',
                'https://music.youtube.com/watch?v=dQw4w9WgXcQ&list=RDAMVM'
            ];
            
            validUrls.forEach(url => {
                expect(urlInput.validateUrl(url)).toBe(true);
            });
        });
        
        test('should reject invalid URLs', () => {
            const invalidUrls = [
                '',
                'not-a-url',
                'https://google.com',
                'https://vimeo.com/123456789',
                'https://youtube.com/channel/UC123',
                'https://youtube.com/user/testuser',
                'https://youtube.com/playlist?list=PLtest',
                'https://youtube.com/watch?v=invalid',
                'https://youtube.com/watch?v=dQw4w9WgX', // too short
                'https://youtube.com/watch?v=dQw4w9WgXcQ123', // too long
                'ftp://youtube.com/watch?v=dQw4w9WgXcQ',
                'https://youtube.com/watch?list=PLtest'
            ];
            
            invalidUrls.forEach(url => {
                expect(urlInput.validateUrl(url)).toBe(false);
            });
        });
    });
    
    describe('Form Handling', () => {
        test('should show error for empty URL', async () => {
            const urlInput_element = document.getElementById('youtube-url');
            urlInput_element.value = '';
            
            await urlInput.handleSubmit();
            
            const errorElement = document.getElementById('url-error');
            expect(errorElement.textContent).toBe('Please enter a YouTube URL');
            expect(errorElement.classList.contains('active')).toBe(true);
        });
        
        test('should show error for invalid URL', async () => {
            const urlInput_element = document.getElementById('youtube-url');
            urlInput_element.value = 'https://google.com';
            
            await urlInput.handleSubmit();
            
            const errorElement = document.getElementById('url-error');
            expect(errorElement.textContent).toBe('Please enter a valid YouTube URL');
            expect(errorElement.classList.contains('active')).toBe(true);
        });
        
        test('should call addQueueItem with valid URL', async () => {
            const urlInput_element = document.getElementById('youtube-url');
            const customPromptElement = document.getElementById('custom-prompt');
            
            urlInput_element.value = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
            customPromptElement.value = 'Test prompt';
            
            // Mock successful API call
            window.app.addQueueItem.mockResolvedValue({ success: true, item_id: 'test-123' });
            
            await urlInput.handleSubmit();
            
            expect(window.app.addQueueItem).toHaveBeenCalledWith(
                'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                'Test prompt'
            );
        });
        
        test('should call addQueueItem with null custom prompt when empty', async () => {
            const urlInput_element = document.getElementById('youtube-url');
            const customPromptElement = document.getElementById('custom-prompt');
            
            urlInput_element.value = 'https://youtu.be/dQw4w9WgXcQ';
            customPromptElement.value = '   '; // whitespace only
            
            // Mock successful API call
            window.app.addQueueItem.mockResolvedValue({ success: true, item_id: 'test-123' });
            
            await urlInput.handleSubmit();
            
            expect(window.app.addQueueItem).toHaveBeenCalledWith(
                'https://youtu.be/dQw4w9WgXcQ',
                null
            );
        });
        
        test('should handle API errors gracefully', async () => {
            const urlInput_element = document.getElementById('youtube-url');
            urlInput_element.value = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
            
            // Mock API error
            window.app.addQueueItem.mockRejectedValue(new Error('Network error'));
            
            await urlInput.handleSubmit();
            
            const errorElement = document.getElementById('url-error');
            expect(errorElement.textContent).toBe('Network error');
            expect(errorElement.classList.contains('active')).toBe(true);
        });
    });
    
    describe('Loading States', () => {
        test('should set loading state during submission', async () => {
            const urlInput_element = document.getElementById('youtube-url');
            urlInput_element.value = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ';
            
            // Mock slow API call
            let resolvePromise;
            const slowPromise = new Promise(resolve => {
                resolvePromise = resolve;
            });
            window.app.addQueueItem.mockReturnValue(slowPromise);
            
            // Start submission
            const submitPromise = urlInput.handleSubmit();
            
            // Check loading state
            const submitButton = document.getElementById('submit-btn');
            const btnText = submitButton.querySelector('.btn-text');
            const btnSpinner = submitButton.querySelector('.btn-spinner');
            
            expect(submitButton.disabled).toBe(true);
            expect(btnText.style.display).toBe('none');
            expect(btnSpinner.style.display).toBe('inline');
            
            // Resolve the API call
            resolvePromise({ success: true, item_id: 'test-123' });
            await submitPromise;
            
            // Check loading state is cleared (may still be disabled briefly)
            // In real implementation, this might still be true due to timing
            expect(btnText.style.display).toBe('inline');
            expect(btnSpinner.style.display).toBe('none');
        });
    });
    
    describe('Modal Functionality', () => {
        test('should show modal', () => {
            const modal = document.getElementById('url-modal-overlay');
            
            urlInput.show();
            
            expect(modal.classList.contains('active')).toBe(true);
        });
        
        test('should hide modal and reset form', () => {
            const modal = document.getElementById('url-modal-overlay');
            const form = document.getElementById('url-form');
            const urlInput_element = document.getElementById('youtube-url');
            const errorElement = document.getElementById('url-error');
            
            // Set some state
            modal.classList.add('active');
            urlInput_element.value = 'test';
            errorElement.classList.add('active');
            errorElement.textContent = 'Test error';
            
            urlInput.hide();
            
            expect(modal.classList.contains('active')).toBe(false);
            expect(urlInput_element.value).toBe('');
            expect(errorElement.classList.contains('active')).toBe(false);
            expect(errorElement.textContent).toBe('');
        });
        
        test('should clear error on input', () => {
            const urlInput_element = document.getElementById('youtube-url');
            const errorElement = document.getElementById('url-error');
            
            // Set error state
            errorElement.classList.add('active');
            errorElement.textContent = 'Test error';
            
            // Simulate input event
            const inputEvent = new Event('input');
            urlInput_element.dispatchEvent(inputEvent);
            
            expect(errorElement.classList.contains('active')).toBe(false);
            expect(errorElement.textContent).toBe('');
        });
    });
});