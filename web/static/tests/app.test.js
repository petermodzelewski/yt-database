/**
 * Unit tests for Main Application
 * 
 * Tests the main app functionality including API integration
 */

// Mock DOM utilities
global.DOMUtils = {
    getElementById: jest.fn(),
    addEventListener: jest.fn(),
    createElement: jest.fn()
};

// Mock components
global.QueueColumns = jest.fn().mockImplementation(() => ({
    render: jest.fn()
}));
global.UrlInput = jest.fn().mockImplementation(() => ({
    show: jest.fn(),
    hide: jest.fn()
}));
global.ChatLogModal = jest.fn().mockImplementation(() => ({
    show: jest.fn(),
    hide: jest.fn()
}));
global.SSEConnection = jest.fn().mockImplementation(() => ({
    connect: jest.fn(),
    disconnect: jest.fn(),
    getStats: jest.fn(() => ({ isConnected: true })),
    reconnect: jest.fn(),
    destroy: jest.fn()
}));

describe('YouTubeNotionApp', () => {
    let app;
    
    beforeEach(() => {
        // Reset DOM
        document.body.innerHTML = `
            <button id="add-url-btn">Add URL</button>
        `;
        
        // Mock getElementById to return actual elements
        DOMUtils.getElementById.mockImplementation((id) => document.getElementById(id));
        
        // Load and initialize the app
        const YouTubeNotionApp = require('../app.js');
        app = new YouTubeNotionApp();
    });
    
    afterEach(() => {
        jest.clearAllMocks();
    });
    
    describe('Initialization', () => {
        test('should initialize components', () => {
            expect(QueueColumns).toHaveBeenCalled();
            expect(UrlInput).toHaveBeenCalled();
            expect(ChatLogModal).toHaveBeenCalled();
        });
        
        test('should setup event listeners', () => {
            expect(DOMUtils.addEventListener).toHaveBeenCalled();
        });
    });
    
    describe('addQueueItem', () => {
        test('should make POST request to /api/queue with URL only', async () => {
            const mockResponse = { success: true, item_id: 'test-123' };
            mockFetchSuccess(mockResponse);
            
            const result = await app.addQueueItem('https://www.youtube.com/watch?v=dQw4w9WgXcQ');
            
            expect(fetch).toHaveBeenCalledWith('/api/queue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
                }),
                signal: expect.any(AbortSignal)
            });
            
            expect(result).toEqual(mockResponse);
        });
        
        test('should make POST request with custom prompt', async () => {
            const mockResponse = { success: true, item_id: 'test-456' };
            mockFetchSuccess(mockResponse);
            
            const result = await app.addQueueItem(
                'https://youtu.be/dQw4w9WgXcQ',
                'Custom summary prompt'
            );
            
            expect(fetch).toHaveBeenCalledWith('/api/queue', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: 'https://youtu.be/dQw4w9WgXcQ',
                    custom_prompt: 'Custom summary prompt'
                }),
                signal: expect.any(AbortSignal)
            });
            
            expect(result).toEqual(mockResponse);
        });
        
        test('should handle HTTP error responses', async () => {
            const errorData = { error: 'Invalid URL format' };
            mockFetchError(400, 'Bad Request', errorData);
            
            await expect(app.addQueueItem('invalid-url')).rejects.toThrow('Invalid URL format');
        });
        
        test('should handle HTTP error responses without error data', async () => {
            mockFetchError(500, 'Internal Server Error');
            
            await expect(app.addQueueItem('https://www.youtube.com/watch?v=dQw4w9WgXcQ'))
                .rejects.toThrow('Server error - please try again later');
        });
        
        test('should handle network errors', async () => {
            mockFetchNetworkError('Failed to fetch');
            
            await expect(app.addQueueItem('https://www.youtube.com/watch?v=dQw4w9WgXcQ'))
                .rejects.toThrow('Failed to fetch');
        });
        
        test('should handle API success=false responses', async () => {
            const mockResponse = { success: false, error: 'Queue is full' };
            mockFetchSuccess(mockResponse);
            
            await expect(app.addQueueItem('https://www.youtube.com/watch?v=dQw4w9WgXcQ'))
                .rejects.toThrow('Queue is full');
        });
        
        test('should handle API success=false responses without error message', async () => {
            const mockResponse = { success: false };
            mockFetchSuccess(mockResponse);
            
            await expect(app.addQueueItem('https://www.youtube.com/watch?v=dQw4w9WgXcQ'))
                .rejects.toThrow('Failed to add URL to queue');
        });
        
        test('should handle malformed JSON responses', async () => {
            fetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                statusText: 'Bad Request',
                json: async () => { throw new Error('Invalid JSON'); }
            });
            
            await expect(app.addQueueItem('https://www.youtube.com/watch?v=dQw4w9WgXcQ'))
                .rejects.toThrow('Invalid request - please check the URL format');
        });
    });
    
    describe('updateQueueDisplay', () => {
        test('should call queueColumns.render with queue data', () => {
            const mockQueueData = {
                todo: [{ id: '1', url: 'test1' }],
                'in-progress': [{ id: '2', url: 'test2' }],
                done: [{ id: '3', url: 'test3' }]
            };
            
            const mockRender = jest.fn();
            app.components.queueColumns = { render: mockRender };
            
            app.updateQueueDisplay(mockQueueData);
            
            expect(mockRender).toHaveBeenCalledWith(mockQueueData);
        });
    });
    
    describe('showChatLog', () => {
        test('should call chatLogModal.show with item ID', () => {
            const mockShow = jest.fn();
            app.components.chatLogModal = { show: mockShow };
            
            app.showChatLog('test-item-123');
            
            expect(mockShow).toHaveBeenCalledWith('test-item-123', null);
        });
        
        test('should call chatLogModal.show with item ID and chunk index', () => {
            const mockShow = jest.fn();
            app.components.chatLogModal = { show: mockShow };
            
            app.showChatLog('test-item-456', 2);
            
            expect(mockShow).toHaveBeenCalledWith('test-item-456', 2);
        });
    });
    
    describe('getComponent', () => {
        test('should return component by name', () => {
            const component = app.getComponent('queueColumns');
            expect(component).toBe(app.components.queueColumns);
        });
        
        test('should return null for non-existent component', () => {
            const component = app.getComponent('nonExistent');
            expect(component).toBeNull();
        });
    });
});