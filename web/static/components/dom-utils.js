/**
 * DOM Utilities
 * 
 * Utility class for DOM manipulation and event handling
 */

class DOMUtils {
    /**
     * Create an element with attributes and content
     * @param {string} tag - HTML tag name
     * @param {Object} attributes - Element attributes
     * @param {string|Node|Array} content - Element content
     * @returns {HTMLElement}
     */
    static createElement(tag, attributes = {}, content = '') {
        const element = document.createElement(tag);
        
        // Set attributes
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
        
        // Set content
        if (typeof content === 'string') {
            element.innerHTML = content;
        } else if (content instanceof Node) {
            element.appendChild(content);
        } else if (Array.isArray(content)) {
            content.forEach(child => {
                if (typeof child === 'string') {
                    element.appendChild(document.createTextNode(child));
                } else if (child instanceof Node) {
                    element.appendChild(child);
                }
            });
        }
        
        return element;
    }

    /**
     * Add event listener with automatic cleanup tracking
     * @param {HTMLElement} element - Target element
     * @param {string} event - Event type
     * @param {Function} handler - Event handler
     * @param {Object} options - Event options
     */
    static addEventListener(element, event, handler, options = {}) {
        element.addEventListener(event, handler, options);
        
        // Store cleanup function for potential future use
        if (!element._eventCleanup) {
            element._eventCleanup = [];
        }
        element._eventCleanup.push(() => {
            element.removeEventListener(event, handler, options);
        });
    }

    /**
     * Remove all event listeners from an element
     * @param {HTMLElement} element - Target element
     */
    static removeAllEventListeners(element) {
        if (element._eventCleanup) {
            element._eventCleanup.forEach(cleanup => cleanup());
            element._eventCleanup = [];
        }
    }

    /**
     * Safely get element by ID with error handling
     * @param {string} id - Element ID
     * @returns {HTMLElement|null}
     */
    static getElementById(id) {
        const element = document.getElementById(id);
        if (!element) {
            console.warn(`Element with ID '${id}' not found`);
        }
        return element;
    }

    /**
     * Animate element with CSS transitions
     * @param {HTMLElement} element - Target element
     * @param {Object} styles - CSS styles to animate to
     * @param {number} duration - Animation duration in ms
     * @returns {Promise}
     */
    static animate(element, styles, duration = 250) {
        return new Promise(resolve => {
            const originalTransition = element.style.transition;
            element.style.transition = `all ${duration}ms ease`;
            
            Object.entries(styles).forEach(([property, value]) => {
                element.style[property] = value;
            });
            
            setTimeout(() => {
                element.style.transition = originalTransition;
                resolve();
            }, duration);
        });
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DOMUtils;
}

// Make available globally
window.DOMUtils = DOMUtils;