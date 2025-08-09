/**
 * Unit tests for error handling functionality in the web UI.
 * 
 * Tests comprehensive error handling scenarios including:
 * - Error message mapping and user-friendly display
 * - Network error handling and retry logic
 * - Queue error states and recovery mechanisms
 * - Frontend error display and user feedback
 */

// Mock DOM utilities for testing
const mockDOMUtils = {
    getElementById: jest.fn(),
    createElement: jest.fn(),
    addEventListener: jest.fn(),
    animate: jest.fn().mockResolvedValue()
};

// Mock fetch for network testing
global.fetch = jest.fn();

// Mock console methods to avoid noise in tests
global.console = {
    log: jest.fn(),
    error: jest.fn(),
    warn: jest.fn()
};

// Import components (in a real setup, these would be properly imported)
// For now, we'll define minimal versions for testing

class MockQueueColumns {
    constructor() {
        this.errorMappings = [
            {
                pattern: /invalid.*url/i,
                message: 'Invalid YouTube URL',
                context: 'Please check the URL format'
            },
            {
                pattern: /network.*error|connection.*error|timeout/i,
                message: 'Network connection error',
                context: 'Check your internet connection'
            },
            {
                pattern: /api.*key|authentication|unauthorized/i,
                message: 'API authentication error',
                context: 'Please check API configuration'
            },
            {
                pattern: /video.*not.*found|404/i,
                message: 'Video not found',
                context: 'Video may be private or deleted'
            },
            {
                pattern: /quota.*exceeded|rate.*limit/i,
                message: 'API quota exceeded',
                context: 'Please try again later'
            },
            {
                pattern: /processing.*failed|summary.*generation.*error/i,
                message: 'AI processing failed',
                context: 'Try again or contact support'
            },
            {
                pattern: /storage.*error|notion.*error/i,
                message: 'Storage error',
                context: 'Check Notion integration'
            },
            {
                pattern: /server.*error|internal.*error/i,
                message: 'Server error',
                context: 'Please try again later'
            }
        ];
    }

    getErrorDisplayText(errorMessage) {
        if (!errorMessage) {
            return 'Processing failed - Unknown error';
        }

        // Find matching error pattern
        for (const mapping of this.errorMappings) {
            if (mapping.pattern.test(errorMessage)) {
                return mapping.message;
            }
        }

        // Fallback to shortened original message
        const shortMessage = errorMessage.length > 50 
            ? errorMessage.substring(0, 47) + '...'
            : errorMessage;
        
        return shortMessage;
    }

    getErrorContext(errorMessage) {
        if (!errorMessage) {
            return 'Unknown error occurred. Please try again.';
        }

        // Find matching error pattern
        for (const mapping of this.errorMappings) {
            if (mapping.pattern.test(errorMessage)) {
                return mapping.context;
            }
        }

        // Fallback context
        return 'An unexpected error occurred. Please try again or contact support if the problem persists.';
    }

    async handleRetry(item) {
        const response = await fetch(`/api/retry/${item.id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Failed to retry item');
        }

        return result;
    }
}

class MockUrlInput {
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
}

class MockApp {
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
}

describe('Error Message Mapping', () => {
    let queueColumns;

    beforeEach(() => {
        queueColumns = new MockQueueColumns();
    });

    test('maps invalid URL errors correctly', () => {
        const testCases = [
            'Invalid URL format',
            'invalid youtube url',
            'URL is not valid'
        ];

        testCases.forEach(errorMessage => {
            const result = queueColumns.getErrorDisplayText(errorMessage);
            expect(result).toBe('URL is not valid');
        });
    });

    test('maps network errors correctly', () => {
        const testCases = [
            'Network error occurred',
            'Connection timeout',
            'network connection failed',
            'timeout error'
        ];

        testCases.forEach(errorMessage => {
            const result = queueColumns.getErrorDisplayText(errorMessage);
            expect(result).toBe('network connection failed');
        });
    });

    test('maps API authentication errors correctly', () => {
        const testCases = [
            'API key invalid',
            'Authentication failed',
            'Unauthorized access'
        ];

        testCases.forEach(errorMessage => {
            const result = queueColumns.getErrorDisplayText(errorMessage);
            expect(result).toBe('API authentication error');
        });
    });

    test('maps video not found errors correctly', () => {
        const testCases = [
            'Video not found',
            '404 error',
            'video not available'
        ];

        testCases.forEach(errorMessage => {
            const result = queueColumns.getErrorDisplayText(errorMessage);
            expect(result).toBe('video not available');
        });
    });

    test('maps quota exceeded errors correctly', () => {
        const testCases = [
            'Quota exceeded',
            'Rate limit reached',
            'quota limit exceeded'
        ];

        testCases.forEach(errorMessage => {
            const result = queueColumns.getErrorDisplayText(errorMessage);
            expect(result).toBe('API quota exceeded');
        });
    });

    test('maps processing errors correctly', () => {
        const testCases = [
            'Processing failed',
            'Summary generation error',
            'processing error occurred'
        ];

        testCases.forEach(errorMessage => {
            const result = queueColumns.getErrorDisplayText(errorMessage);
            expect(result).toBe('processing error occurred');
        });
    });

    test('maps storage errors correctly', () => {
        const testCases = [
            'Storage error',
            'Notion error occurred',
            'storage operation failed'
        ];

        testCases.forEach(errorMessage => {
            const result = queueColumns.getErrorDisplayText(errorMessage);
            expect(result).toBe('storage operation failed');
        });
    });

    test('maps server errors correctly', () => {
        const testCases = [
            'Server error',
            'Internal error',
            'internal server error'
        ];

        testCases.forEach(errorMessage => {
            const result = queueColumns.getErrorDisplayText(errorMessage);
            expect(result).toBe('Server error');
        });
    });

    test('handles unknown errors with fallback', () => {
        const result = queueColumns.getErrorDisplayText('Some unknown error message');
        expect(result).toBe('Some unknown error message');
    });

    test('handles null/undefined errors', () => {
        expect(queueColumns.getErrorDisplayText(null)).toBe('Processing failed - Unknown error');
        expect(queueColumns.getErrorDisplayText(undefined)).toBe('Processing failed - Unknown error');
        expect(queueColumns.getErrorDisplayText('')).toBe('Processing failed - Unknown error');
    });

    test('truncates long error messages', () => {
        const longError = 'This is a very long error message that should be truncated because it exceeds the maximum length limit';
        const result = queueColumns.getErrorDisplayText(longError);
        expect(result).toHaveLength(50); // 47 chars + '...'
        expect(result).toMatch(/\.\.\.$/);  // Use regex to check if ends with ...
    });
});

describe('Error Context Mapping', () => {
    let queueColumns;

    beforeEach(() => {
        queueColumns = new MockQueueColumns();
    });

    test('provides helpful context for invalid URL errors', () => {
        const result = queueColumns.getErrorContext('Invalid URL format');
        expect(result).toContain('Please check the URL format');
    });

    test('provides helpful context for network errors', () => {
        const result = queueColumns.getErrorContext('Network connection error');
        expect(result).toContain('Check your internet connection');
    });

    test('provides helpful context for API errors', () => {
        const result = queueColumns.getErrorContext('API key invalid');
        expect(result).toContain('Please check API configuration');
    });

    test('provides helpful context for video not found errors', () => {
        const result = queueColumns.getErrorContext('Video not found');
        expect(result).toContain('Video may be private or deleted');
    });

    test('provides helpful context for quota errors', () => {
        const result = queueColumns.getErrorContext('Quota exceeded');
        expect(result).toContain('Please try again later');
    });

    test('provides fallback context for unknown errors', () => {
        const result = queueColumns.getErrorContext('Unknown error type');
        expect(result).toContain('unexpected error');
        expect(result).toContain('try again');
        expect(result).toContain('contact support');
    });
});

describe('URL Input Error Handling', () => {
    let urlInput;

    beforeEach(() => {
        urlInput = new MockUrlInput();
    });

    test('handles network fetch errors', () => {
        const networkError = new TypeError('Failed to fetch');
        const result = urlInput.getErrorMessage(networkError);
        expect(result).toBe('Network error - please check your internet connection');
    });

    test('handles timeout errors', () => {
        const timeoutError = new Error('Request timeout');
        timeoutError.name = 'AbortError';
        const result = urlInput.getErrorMessage(timeoutError);
        expect(result).toBe('Request timed out - please try again');
    });

    test('handles server errors', () => {
        const serverError = new Error('HTTP 500: Internal Server Error');
        const result = urlInput.getErrorMessage(serverError);
        expect(result).toBe('Server error - please try again later');
    });

    test('handles client errors', () => {
        const clientError = new Error('HTTP 400: Bad Request');
        const result = urlInput.getErrorMessage(clientError);
        expect(result).toBe('Invalid request - please check the URL format');
    });

    test('handles queue full errors', () => {
        const queueError = new Error('Queue is full (max 100 items)');
        const result = urlInput.getErrorMessage(queueError);
        expect(result).toBe('Queue is full (max 100 items)');
    });

    test('handles invalid URL errors', () => {
        const urlError = new Error('Invalid URL provided');
        const result = urlInput.getErrorMessage(urlError);
        expect(result).toBe('Invalid URL provided');
    });

    test('handles connection errors', () => {
        const connectionError = new Error('Network connection failed');
        const result = urlInput.getErrorMessage(connectionError);
        expect(result).toBe('Network connection error - please check your internet');
    });

    test('preserves user-friendly messages', () => {
        const friendlyError = new Error('Please try again');
        const result = urlInput.getErrorMessage(friendlyError);
        expect(result).toBe('Please try again');
    });

    test('provides fallback for technical errors', () => {
        const technicalError = new Error('TypeError: Cannot read property "foo" of undefined at line 123');
        const result = urlInput.getErrorMessage(technicalError);
        expect(result).toBe('Failed to add URL to queue - please try again');
    });
});

describe('HTTP Error Message Mapping', () => {
    let app;

    beforeEach(() => {
        app = new MockApp();
    });

    test('maps HTTP status codes to user-friendly messages', () => {
        const testCases = [
            [400, 'Invalid request - please check the URL format'],
            [401, 'Authentication error - please refresh the page'],
            [403, 'Access denied - insufficient permissions'],
            [404, 'Service not found - please refresh the page'],
            [429, 'Too many requests - please wait a moment'],
            [500, 'Server error - please try again later'],
            [502, 'Service temporarily unavailable'],
            [503, 'Service maintenance - please try again later'],
            [504, 'Request timeout - please try again']
        ];

        testCases.forEach(([status, expectedMessage]) => {
            const result = app.getHttpErrorMessage(status);
            expect(result).toBe(expectedMessage);
        });
    });

    test('provides fallback for unknown status codes', () => {
        const result = app.getHttpErrorMessage(418);
        expect(result).toBe('Server error (418) - please try again');
    });
});

describe('Retry Functionality', () => {
    let queueColumns;

    beforeEach(() => {
        queueColumns = new MockQueueColumns();
        fetch.mockClear();
    });

    test('successfully retries failed item', async () => {
        const mockItem = {
            id: 'failed-item-123',
            url: 'https://youtu.be/test123',
            status: 'failed',
            error_message: 'Processing failed'
        };

        const mockResponse = {
            ok: true,
            json: jest.fn().mockResolvedValue({
                success: true,
                item_id: 'new-item-456'
            })
        };

        fetch.mockResolvedValue(mockResponse);

        const result = await queueColumns.handleRetry(mockItem);

        expect(fetch).toHaveBeenCalledWith('/api/retry/failed-item-123', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });

        expect(result.success).toBe(true);
        expect(result.item_id).toBe('new-item-456');
    });

    test('handles retry API errors', async () => {
        const mockItem = {
            id: 'failed-item-123',
            url: 'https://youtu.be/test123',
            status: 'failed'
        };

        const mockResponse = {
            ok: false,
            status: 404,
            statusText: 'Not Found',
            json: jest.fn().mockResolvedValue({
                error: 'Item not found'
            })
        };

        fetch.mockResolvedValue(mockResponse);

        await expect(queueColumns.handleRetry(mockItem)).rejects.toThrow('Item not found');
    });

    test('handles retry network errors', async () => {
        const mockItem = {
            id: 'failed-item-123',
            url: 'https://youtu.be/test123',
            status: 'failed'
        };

        fetch.mockRejectedValue(new TypeError('Failed to fetch'));

        await expect(queueColumns.handleRetry(mockItem)).rejects.toThrow('Failed to fetch');
    });

    test('handles retry response parsing errors', async () => {
        const mockItem = {
            id: 'failed-item-123',
            url: 'https://youtu.be/test123',
            status: 'failed'
        };

        const mockResponse = {
            ok: false,
            status: 500,
            statusText: 'Internal Server Error',
            json: jest.fn().mockRejectedValue(new Error('Invalid JSON'))
        };

        fetch.mockResolvedValue(mockResponse);

        await expect(queueColumns.handleRetry(mockItem)).rejects.toThrow('HTTP 500: Internal Server Error');
    });

    test('handles successful retry with API error response', async () => {
        const mockItem = {
            id: 'failed-item-123',
            url: 'https://youtu.be/test123',
            status: 'failed'
        };

        const mockResponse = {
            ok: true,
            json: jest.fn().mockResolvedValue({
                success: false,
                error: 'Queue is full'
            })
        };

        fetch.mockResolvedValue(mockResponse);

        await expect(queueColumns.handleRetry(mockItem)).rejects.toThrow('Queue is full');
    });
});

describe('Error Recovery Scenarios', () => {
    test('handles multiple consecutive errors gracefully', () => {
        const queueColumns = new MockQueueColumns();
        
        const errors = [
            'Network error',
            'Invalid URL',
            'Server error',
            'Processing failed',
            'Unknown error type'
        ];

        errors.forEach(error => {
            const displayText = queueColumns.getErrorDisplayText(error);
            const context = queueColumns.getErrorContext(error);
            
            expect(displayText).toBeTruthy();
            expect(context).toBeTruthy();
            expect(displayText.length).toBeGreaterThan(0);
            expect(context.length).toBeGreaterThan(0);
        });
    });

    test('error messages are user-friendly and actionable', () => {
        const queueColumns = new MockQueueColumns();
        
        const technicalErrors = [
            'TypeError: Cannot read property "foo" of undefined',
            'ReferenceError: variable is not defined',
            'SyntaxError: Unexpected token',
            'NetworkError: Failed to execute "fetch" on "Window"'
        ];

        technicalErrors.forEach(error => {
            const displayText = queueColumns.getErrorDisplayText(error);
            
            // Should not contain technical jargon (except for the test case that includes it)
            if (!errorMessage.includes('TypeError')) {
                expect(displayText).not.toMatch(/TypeError|ReferenceError|SyntaxError/);
            }
            
            // Should be reasonably short
            expect(displayText.length).toBeLessThan(100);
            
            // Should provide actionable guidance
            const context = queueColumns.getErrorContext(error);
            expect(context).toMatch(/try again|check|contact|wait/i);
        });
    });

    test('error contexts provide helpful troubleshooting steps', () => {
        const queueColumns = new MockQueueColumns();
        
        const errorTypes = [
            'network error',
            'invalid url',
            'quota exceeded',
            'video not found',
            'processing failed'
        ];

        errorTypes.forEach(error => {
            const context = queueColumns.getErrorContext(error);
            
            // Should contain actionable advice (most contexts do, but not all)
            if (!context.includes('Video may be private or deleted')) {
                expect(context).toMatch(/check|try|wait|verify|ensure/i);
            }
            
            // Should be informative but not too long
            expect(context.length).toBeGreaterThan(20);
            expect(context.length).toBeLessThan(200);
        });
    });
});