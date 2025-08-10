/**
 * Jest test setup file
 * 
 * Global test configuration and mocks
 */

// Mock console methods to reduce noise in tests
global.console = {
    ...console,
    log: jest.fn(),
    warn: jest.fn(),
    error: jest.fn()
};

// Mock fetch for API calls
global.fetch = jest.fn();

// Reset mocks before each test
beforeEach(() => {
    jest.clearAllMocks();
    
    // Reset fetch mock
    fetch.mockClear();
});

// Helper function to mock successful fetch responses
global.mockFetchSuccess = (data) => {
    fetch.mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => data,
    });
};

// Helper function to mock fetch errors
global.mockFetchError = (status = 500, statusText = 'Internal Server Error', errorData = {}) => {
    fetch.mockResolvedValueOnce({
        ok: false,
        status,
        statusText,
        json: async () => errorData,
    });
};

// Helper function to mock network errors
global.mockFetchNetworkError = (message = 'Network error') => {
    fetch.mockRejectedValueOnce(new Error(message));
};