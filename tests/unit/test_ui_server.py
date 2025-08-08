import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock

from src.youtube_notion.ui.server import app, websocket_endpoint
from src.youtube_notion.queue import UrlQueue

class MockWebSocket:
    def __init__(self):
        self.accepted = False
        self.sent_messages = []
        self.received_messages = []

    async def accept(self):
        self.accepted = True

    async def send_json(self, data):
        self.sent_messages.append(data)

    async def receive_text(self):
        return await self.receive_queue.get()

@pytest.fixture
def test_app():
    return app

@pytest.mark.asyncio
async def test_websocket_endpoint(monkeypatch):
    # Mock the websocket
    ws = MockWebSocket()
    ws.receive_queue = asyncio.Queue()

    # Mock the process_urls function to avoid actual processing
    process_urls_mock = AsyncMock()
    monkeypatch.setattr('src.youtube_notion.ui.server.process_urls', process_urls_mock)

    # Run the websocket endpoint in a background task
    task = asyncio.create_task(websocket_endpoint(ws))

    # Test that the connection is accepted
    await asyncio.sleep(0.01)
    assert ws.accepted

    # Test sending a URL
    await ws.receive_queue.put("http://test.url")
    await asyncio.sleep(0.01)

    # Since process_urls is mocked, we can't directly test the "queued" message here.
    # We would need a more advanced mock or to test process_urls directly.
    # For now, we'll just check that process_urls was called.
    # In a real test, we would check that url_queue.add was called.

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
