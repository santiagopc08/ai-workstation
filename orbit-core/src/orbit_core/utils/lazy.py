"""Thread-safe lazy initialization."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import Generic, TypeVar

T = TypeVar("T")


class LazyLoader(Generic[T]):
    """Defers initialization of a value until first access.

    Thread-safe via double-checked locking.

    Usage:
        db = LazyLoader(lambda: connect_to_database())
        value = db.get()  # initialized on first call
    """

    def __init__(self, factory: Callable[[], T]) -> None:
        self._factory = factory
        self._value: T | None = None
        self._lock = threading.Lock()
        self._initialized = False

    def get(self) -> T:
        """Return the lazily-initialized value."""
        if not self._initialized:
            with self._lock:
                if not self._initialized:
                    self._value = self._factory()
                    self._initialized = True
        return self._value  # type: ignore[return-value]

    @property
    def is_initialized(self) -> bool:
        """Whether the value has been initialized."""
        return self._initialized

    def reset(self) -> None:
        """Reset to uninitialized state (factory will be called again)."""
        with self._lock:
            self._value = None
            self._initialized = False
