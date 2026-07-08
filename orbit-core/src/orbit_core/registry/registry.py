"""Central component registry — dynamic registration and lookup."""

from __future__ import annotations

from typing import Any

from orbit_core.exceptions.errors import CapabilityError


class ComponentRegistry:
    """Thread-compatible registry for capabilities, providers, and plugins.

    Stores components by string key. No global state — instantiate per context.
    """

    def __init__(self) -> None:
        self._entries: dict[str, Any] = {}

    def register(self, key: str, instance: Any) -> None:
        """Register a component by key. Raises on duplicate."""
        if key in self._entries:
            raise CapabilityError(f"Key already registered: {key}")
        self._entries[key] = instance

    def resolve(self, key: str) -> Any:
        """Resolve a registered component. Raises if not found."""
        if key not in self._entries:
            raise CapabilityError(f"Key not found: {key}")
        return self._entries[key]

    def has(self, key: str) -> bool:
        """Check if a key is registered."""
        return key in self._entries

    def list_all(self) -> list[str]:
        """Return all registered keys."""
        return list(self._entries.keys())

    def unregister(self, key: str) -> None:
        """Remove a registered component. No-op if missing."""
        self._entries.pop(key, None)

    def clear(self) -> None:
        """Remove all registrations."""
        self._entries.clear()

    @property
    def count(self) -> int:
        """Number of registered entries."""
        return len(self._entries)
