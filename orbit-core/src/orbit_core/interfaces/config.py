"""Configuration loader protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ConfigLoader(Protocol):
    """Loads configuration from an external source."""

    def load(self, source: str) -> dict[str, Any]:
        """Load and return configuration as a flat dictionary."""
        ...
