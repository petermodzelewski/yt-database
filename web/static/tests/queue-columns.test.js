/**
 * Unit Tests for QueueColumns Component
 */

require('../components/dom-utils.js');
const QueueColumns = require('../components/queue-columns.js');

describe('QueueColumns Component', () => {
    let queueColumns;

    beforeEach(() => {
        document.body.innerHTML = `
            <div id="todo-items"></div>
            <div id="in-progress-items"></div>
            <div id="done-items"></div>
            <div id="todo-count"></div>
            <div id="in-progress-count"></div>
            <div id="done-count"></div>
            <div id="total-count"></div>
            <div id="processing-count"></div>
        `;
        queueColumns = new QueueColumns();
    });

    it('should render a "To Do" item in a loading state', () => {
        const queueData = {
            todo: [{ id: '1', status: 'todo', url: 'http://a.b' }]
        };
        queueColumns.render(queueData);

        const item = document.querySelector('[data-item-id="1"]');
        expect(item).not.toBeNull();
        expect(item.querySelector('.item-title').textContent).toBe('Loading...');
    });

    it('should render an "In Progress" item with full metadata', () => {
        const queueData = {
            'in-progress': [{
                id: '2',
                status: 'in_progress',
                title: 'Test Title',
                thumbnail_url: 'http://a.b/thumb.jpg'
            }]
        };
        queueColumns.render(queueData);

        const item = document.querySelector('[data-item-id="2"]');
        expect(item).not.toBeNull();
        expect(item.querySelector('.item-title').textContent).toBe('Test Title');
        expect(item.querySelector('.item-thumbnail img').src).toBe('http://a.b/thumb.jpg');
    });

    it('should render a "Done" item', () => {
        const queueData = {
            done: [{
                id: '3',
                status: 'completed',
                title: 'Done Title'
            }]
        };
        queueColumns.render(queueData);

        const item = document.querySelector('[data-item-id="3"]');
        expect(item).not.toBeNull();
        expect(item.querySelector('.item-title').textContent).toBe('Done Title');
    });

    it('should render a "Failed" item', () => {
        const queueData = {
            done: [{
                id: '4',
                status: 'failed',
                title: 'Failed Title',
                error_message: 'It failed'
            }]
        };
        queueColumns.render(queueData);

        const item = document.querySelector('[data-item-id="4"]');
        expect(item).not.toBeNull();
        expect(item.querySelector('.item-title').textContent).toBe('Failed Title');
    });

    it('should clear a column if no items are provided', () => {
        // First render with an item
        const initialData = {
            todo: [{ id: '5', status: 'todo' }]
        };
        queueColumns.render(initialData);
        expect(document.querySelector('[data-item-id="5"]')).not.toBeNull();

        // Second render with no items for that column
        const updatedData = {
            todo: []
        };
        queueColumns.render(updatedData);
        expect(document.querySelector('[data-item-id="5"]')).toBeNull();
    });
});
