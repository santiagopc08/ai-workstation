"""Engine protocol — the top-level contract for any ORBIT engine."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from orbit_core.types.models import HealthStatus


@runtime_checkable
class Engine(Protocol):
    """Top-level contract that every ORBIT engine must satisfy."""

    @property
    def name(self) -> str:
        """Unique engine name."""
        ...

    @property
    def version(self) -> str:
        """Semantic version string."""
        ...

    def initialize(self) -> None:
        """Start the engine, acquire resources."""
        ...

    def shutdown(self) -> None:
        """Stop the engine, release resources."""
        ...

    def health(self) -> HealthStatus:
        """Return engine health status."""
        ...
