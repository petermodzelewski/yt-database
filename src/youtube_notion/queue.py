import queue
from typing import Any, Callable

class UrlQueue:
    def __init__(self):
        self._queue = queue.Queue()
        self._listeners = []

    def add(self, item: Any):
        self._queue.put(item)
        self._notify('add', item)

    def get(self) -> Any:
        return self._queue.get()

    def get_nowait(self) -> Any:
        return self._queue.get_nowait()

    def task_done(self):
        self._queue.task_done()

    def subscribe(self, listener: Callable):
        self._listeners.append(listener)

    def _notify(self, event: str, data: Any):
        for listener in self._listeners:
            listener(event, data)
