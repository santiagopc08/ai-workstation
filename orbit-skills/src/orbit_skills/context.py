"""ORBIT Skills — Context and Capability Resolution.

SkillContext resolves capabilities dynamically.
No hardcoded engine references. No context.git or context.execution.
"""

from __future__ import annotations

from typing import Any

from orbit_core.events import EventBus
from orbit_core.logging import get_logger

from orbit_skills.models import CapabilityId, SkillError

_log = get_logger("skills.context")


class CapabilityRegistry:
    """Maps CapabilityId strings to concrete engine instances.

    Engines are registered once at bootstrap, never hardcoded.
    """

    def __init__(self) -> None:
        self._capabilities: dict[CapabilityId, Any] = {}

    def register(self, capability_id: CapabilityId, provider: Any) -> None:
        """Register a capability provider."""
        self._capabilities[capability_id] = provider
        _log.info(f"Capability registered: {capability_id}")

    def resolve(self, capability_id: CapabilityId) -> Any:
        """Resolve a capability by its ID. Raises SkillError if not found."""
        if capability_id not in self._capabilities:
            raise SkillError(
                skill_id="",
                message=f"Capability not found: {capability_id}",
                code="CAPABILITY_NOT_FOUND",
            )
        return self._capabilities[capability_id]

    def has(self, capability_id: CapabilityId) -> bool:
        """Check whether a capability is registered."""
        return capability_id in self._capabilities

    def list_capabilities(self) -> list[CapabilityId]:
        """Return all registered capability IDs."""
        return list(self._capabilities.keys())


class OrbitSkillContext:
    """Runtime environment passed to Skills during execution.

    Implements the SkillContext protocol from the frozen architecture.
    Uses generic resolve() — no context.git, context.execution, etc.
    """

    def __init__(self, capability_registry: CapabilityRegistry, event_bus: EventBus) -> None:
        self._registry = capability_registry
        self._event_bus = event_bus

    def resolve(self, capability: CapabilityId) -> Any:
        """Dynamically resolve a requested capability ID to the concrete engine interface."""
        return self._registry.resolve(capability)

    @property
    def events(self) -> EventBus:
        """Access the platform event bus."""
        return self._event_bus
