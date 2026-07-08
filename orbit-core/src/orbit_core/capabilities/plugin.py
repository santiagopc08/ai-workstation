"""Plugin protocol — bundles of capabilities that register into the platform."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from orbit_core.capabilities.capability import Capability


@runtime_checkable
class Plugin(Protocol):
    """A plugin that bundles capabilities and registers them."""

    @property
    def id(self) -> str: ...

    @property
    def name(self) -> str: ...

    @property
    def capabilities(self) -> list[Capability]: ...

    def register(self, registry: object) -> None:
        """Register all plugin capabilities into a registry."""
        ...
