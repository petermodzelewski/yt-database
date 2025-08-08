import pytest
from src.youtube_notion.queue import UrlQueue

class TestUrlQueue:
    def test_add_and_get(self):
        queue = UrlQueue()
        queue.add("item1")
        assert queue.get() == "item1"

    def test_get_nowait(self):
        queue = UrlQueue()
        queue.add("item1")
        assert queue.get_nowait() == "item1"

    def test_get_nowait_empty(self):
        queue = UrlQueue()
        with pytest.raises(Exception):
            queue.get_nowait()

    def test_subscribe_and_notify(self):
        queue = UrlQueue()
        received_events = []

        def listener(event, data):
            received_events.append((event, data))

        queue.subscribe(listener)
        queue.add("item1")

        assert len(received_events) == 1
        assert received_events[0] == ("add", "item1")
