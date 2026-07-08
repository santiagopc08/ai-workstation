"""Synchronous, in-memory, typed event bus.

No asyncio. No brokers. No external dependencies.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


class EventBus:
    """Publish-subscribe event bus operating entirely in memory.

    Events are dispatched synchronously to all registered listeners.
    Listener failures are silently swallowed to prevent cascading errors.
    """

    def __init__(self) -> None:
        self._listeners: dict[type[Any], list[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: type[T], callback: Callable[[T], None]) -> None:
        """Register a callback for a specific event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        if callback not in self._listeners[event_type]:
            self._listeners[event_type].append(callback)

    def unsubscribe(self, event_type: type[T], callback: Callable[[T], None]) -> None:
        """Remove a previously registered callback."""
        if event_type in self._listeners:
            with contextlib.suppress(ValueError):
                self._listeners[event_type].remove(callback)

    def publish(self, event: Any) -> None:
        """Dispatch an event to all registered listeners for its type."""
        event_type = type(event)
        for callback in self._listeners.get(event_type, []):
            try:
                callback(event)
            except Exception:  # noqa: BLE001
                # Never let a listener crash the publisher
                continue

    def clear(self) -> None:
        """Remove all registered listeners."""
        self._listeners.clear()

    @property
    def listener_count(self) -> int:
        """Total number of registered callbacks across all event types."""
        return sum(len(cbs) for cbs in self._listeners.values())
