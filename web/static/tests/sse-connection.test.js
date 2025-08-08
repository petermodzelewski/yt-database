/**
 * SSE Connection Component Tests
 */

// Load required components
require('../components/dom-utils.js');
require('../components/sse-connection.js');

// Mock EventSource for testing
class MockEventSource {
    constructor(url) {
        this.url = url;
        this.readyState = EventSource.CONNECTING;
        this.onopen = null;
        this.onmessage = null;
        this.onerror = null;
        
        // Simulate connection after a short delay
        setTimeout(() => {
            this.readyState = EventSource.OPEN;
            if (this.onopen) {
                this.onopen(new Event('open'));
            }
        }, 10);
    }
    
    close() {
        this.readyState = EventSource.CLOSED;
    }
    
    // Helper method for testing
    simulateMessage(data) {
        if (this.onmessage) {
            this.onmessage({ data: JSON.stringify(data) });
        }
    }
    
    simulateError() {
        if (this.onerror) {
            this.onerror(new Event('error'));
        }
    }
}

// Mock global EventSource
global.EventSource = MockEventSource;
MockEventSource.CONNECTING = 0;
MockEventSource.OPEN = 1;
MockEventSource.CLOSED = 2;

describe('SSEConnection', () => {
    let sseConnection;
    let mockApp;
    let mockQueueColumns;
    
    beforeEach(() => {
        // Setup DOM
        document.body.innerHTML = `
            <div class="header-stats"></div>
            <div id="todo-items"></div>
            <div id="in-progress-items"></div>
            <div id="done-items"></div>
            <div id="todo-count">0</div>
            <div id="in-progress-count">0</div>
            <div id="done-count">0</div>
            <div id="total-count">0</div>
            <div id="processing-count">0</div>
        `;
        
        // Mock queue columns component
        mockQueueColumns = {
            createQueueItemElement: jest.fn().mockReturnValue(document.createElement('div'))
        };
        
        // Mock app
        mockApp = {
            updateQueueDisplay: jest.fn(),
            getComponent: jest.fn().mockReturnValue(mockQueueColumns)
        };
        
        // Create SSE connection
        sseConnection = new SSEConnection(mockApp);
    });
    
    afterEach(() => {
        if (sseConnection) {
            sseConnection.destroy();
        }
        jest.clearAllMocks();
    });
    
    describe('Connection Management', () => {
        test('should initialize and connect to SSE endpoint', () => {
            expect(sseConnection.eventSource).toBeDefined();
            expect(sseConnection.eventSource.url).toBe('/events');
        });
        
        test('should handle successful connection', (done) => {
            setTimeout(() => {
                expect(sseConnection.isConnected).toBe(true);
                expect(sseConnection.reconnectAttempts).toBe(0);
                done();
            }, 20);
        });
        
        test('should disconnect properly', () => {
            sseConnection.disconnect();
            expect(sseConnection.isConnected).toBe(false);
            expect(sseConnection.eventSource).toBeNull();
        });
        
        test('should handle connection errors and schedule reconnect', () => {
            const scheduleReconnectSpy = jest.spyOn(sseConnection, 'scheduleReconnect');
            
            sseConnection.eventSource.simulateError();
            
            expect(sseConnection.isConnected).toBe(false);
            expect(scheduleReconnectSpy).toHaveBeenCalled();
        });
    });
    
    describe('Message Handling', () => {
        test('should handle queue status updates', () => {
            const queueData = {
                type: 'queue_status',
                data: {
                    todo: [{ id: '1', status: 'todo' }],
                    in_progress: [{ id: '2', status: 'in_progress' }],
                    completed: [{ id: '3', status: 'completed' }]
                }
            };
            
            sseConnection.eventSource.simulateMessage(queueData);
            
            expect(mockApp.updateQueueDisplay).toHaveBeenCalledWith({
                'todo': queueData.data.todo,
                'in-progress': queueData.data.in_progress,
                'done': queueData.data.completed
            });
        });
        
        test('should handle status change events', () => {
            // Add an item to the DOM first
            const todoItems = document.getElementById('todo-items');
            const itemElement = document.createElement('div');
            itemElement.setAttribute('data-item-id', 'test-item');
            itemElement.className = 'queue-item';
            todoItems.appendChild(itemElement);
            
            const statusChangeData = {
                type: 'status_change',
                data: {
                    item_id: 'test-item',
                    item: {
                        id: 'test-item',
                        status: 'in_progress',
                        title: 'Test Video'
                    }
                }
            };
            
            const animateItemMovementSpy = jest.spyOn(sseConnection, 'animateItemMovement');
            
            sseConnection.eventSource.simulateMessage(statusChangeData);
            
            expect(animateItemMovementSpy).toHaveBeenCalledWith(
                'test-item',
                'todo',
                'in-progress',
                statusChangeData.data.item
            );
        });
        
        test('should handle heartbeat messages', () => {
            const initialHeartbeat = sseConnection.lastHeartbeat || 0;
            
            sseConnection.eventSource.simulateMessage({
                type: 'heartbeat',
                timestamp: new Date().toISOString()
            });
            
            expect(sseConnection.lastHeartbeat).toBeGreaterThan(initialHeartbeat);
        });
        
        test('should handle error messages', () => {
            const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
            
            sseConnection.eventSource.simulateMessage({
                type: 'error',
                error: 'Test error message'
            });
            
            expect(consoleSpy).toHaveBeenCalledWith(
                'SSEConnection: Server error:',
                'Test error message'
            );
            
            consoleSpy.mockRestore();
        });
    });
    
    describe('Status Mapping', () => {
        test('should map server status to frontend columns correctly', () => {
            expect(sseConnection.mapStatusToColumn('todo')).toBe('todo');
            expect(sseConnection.mapStatusToColumn('in_progress')).toBe('in-progress');
            expect(sseConnection.mapStatusToColumn('completed')).toBe('done');
            expect(sseConnection.mapStatusToColumn('failed')).toBe('done');
            expect(sseConnection.mapStatusToColumn('unknown')).toBe('todo');
        });
    });
    
    describe('Item Location', () => {
        test('should find current column of an item', () => {
            // Add item to in-progress column
            const inProgressItems = document.getElementById('in-progress-items');
            const itemElement = document.createElement('div');
            itemElement.setAttribute('data-item-id', 'test-item');
            inProgressItems.appendChild(itemElement);
            
            const column = sseConnection.findItemCurrentColumn('test-item');
            expect(column).toBe('in-progress');
        });
        
        test('should return null for non-existent item', () => {
            const column = sseConnection.findItemCurrentColumn('non-existent');
            expect(column).toBeNull();
        });
    });
    
    describe('Counter Updates', () => {
        test('should update column counters correctly', () => {
            // Add some items to columns
            const todoItems = document.getElementById('todo-items');
            const inProgressItems = document.getElementById('in-progress-items');
            
            for (let i = 0; i < 3; i++) {
                const item = document.createElement('div');
                item.className = 'queue-item';
                todoItems.appendChild(item);
            }
            
            for (let i = 0; i < 2; i++) {
                const item = document.createElement('div');
                item.className = 'queue-item';
                inProgressItems.appendChild(item);
            }
            
            sseConnection.updateColumnCounters();
            
            expect(document.getElementById('todo-count').textContent).toBe('3');
            expect(document.getElementById('in-progress-count').textContent).toBe('2');
            expect(document.getElementById('done-count').textContent).toBe('0');
            expect(document.getElementById('total-count').textContent).toBe('5');
            expect(document.getElementById('processing-count').textContent).toBe('2');
        });
    });
    
    describe('Reconnection Logic', () => {
        test('should implement exponential backoff', (done) => {
            const initialDelay = sseConnection.reconnectDelay;
            
            // Mock setTimeout to capture the delay calculation
            const originalSetTimeout = global.setTimeout;
            global.setTimeout = jest.fn((callback, delay) => {
                // The delay should be calculated with exponential backoff
                expect(delay).toBeGreaterThanOrEqual(initialDelay);
                
                // Restore setTimeout
                global.setTimeout = originalSetTimeout;
                done();
                
                return 123; // Mock timer ID
            });
            
            sseConnection.scheduleReconnect();
        });
        
        test('should stop reconnecting after max attempts', () => {
            sseConnection.reconnectAttempts = sseConnection.maxReconnectAttempts;
            
            const updateConnectionStatusSpy = jest.spyOn(sseConnection, 'updateConnectionStatus');
            
            sseConnection.scheduleReconnect();
            
            expect(updateConnectionStatusSpy).toHaveBeenCalledWith(
                false,
                'Connection failed after multiple attempts'
            );
        });
    });
    
    describe('Connection Status UI', () => {
        test('should create and update connection indicator', () => {
            sseConnection.updateConnectionStatus(true);
            
            const indicator = document.getElementById('connection-indicator');
            expect(indicator).toBeDefined();
            expect(indicator.className).toContain('connected');
            expect(indicator.textContent).toContain('Connected');
        });
        
        test('should show disconnected status', () => {
            sseConnection.updateConnectionStatus(false, 'Test error');
            
            const indicator = document.getElementById('connection-indicator');
            expect(indicator.className).toContain('disconnected');
            expect(indicator.textContent).toContain('Test error');
        });
    });
    
    describe('Statistics', () => {
        test('should provide connection statistics', () => {
            const stats = sseConnection.getStats();
            
            expect(stats).toHaveProperty('isConnected');
            expect(stats).toHaveProperty('reconnectAttempts');
            expect(stats).toHaveProperty('lastHeartbeat');
            expect(stats).toHaveProperty('timeSinceLastHeartbeat');
        });
    });
    
    describe('Cleanup', () => {
        test('should cleanup properly on destroy', () => {
            const disconnectSpy = jest.spyOn(sseConnection, 'disconnect');
            
            sseConnection.destroy();
            
            expect(disconnectSpy).toHaveBeenCalled();
        });
    });
});