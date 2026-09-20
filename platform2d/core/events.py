"""Synchronous notifications, independent of rendering and game rules."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    kind: str
    source: tuple[str, str]


class EventBus:
    def __init__(self):
        self.listeners = {}

    def subscribe(self, kind, callback):
        listeners = self.listeners.setdefault(kind, [])
        listeners.append(callback)
        def unsubscribe():
            if callback in listeners:
                listeners.remove(callback)
        return unsubscribe

    def publish(self, event):
        for callback in tuple(self.listeners.get(event.kind, ())):
            callback(event)
