"""Capability — a self-describing, lifecycle-managed unit of functionality."""

from __future__ import annotations

from dataclasses import dataclass, field

from orbit_core.types.models import HealthStatus


@dataclass(slots=True)
class Capability:
    """Represents a discrete unit of platform functionality.

    Each engine registers one or more capabilities that describe
    what it can do, its dependencies, and its lifecycle.
    """

    id: str
    name: str
    description: str
    version: str
    dependencies: list[str] = field(default_factory=list)
    _initialized: bool = field(default=False, repr=False)

    def initialize(self) -> None:
        """Start the capability."""
        self._initialized = True

    def shutdown(self) -> None:
        """Stop the capability."""
        self._initialized = False

    def health(self) -> HealthStatus:
        """Return capability health."""
        status = "healthy" if self._initialized else "stopped"
        return HealthStatus(
            status=status,
            version=self.version,
        )
