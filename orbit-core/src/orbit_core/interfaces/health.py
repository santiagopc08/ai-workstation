"""Health check protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from orbit_core.types.models import HealthStatus


@runtime_checkable
class HealthCheck(Protocol):
    """Any component that can report its health."""

    def health(self) -> HealthStatus:
        """Return current health status."""
        ...
