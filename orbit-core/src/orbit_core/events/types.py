"""Base event types for the ORBIT platform."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class Event:
    """Base event — all platform events extend this."""

    source: str = ""
    timestamp: float = field(default_factory=time.time)


@dataclass(frozen=True, slots=True)
class LifecycleEvent(Event):
    """Lifecycle state change event."""

    state: str = ""  # "starting", "started", "stopping", "stopped"
    component: str = ""


@dataclass(frozen=True, slots=True)
class HealthChanged(Event):
    """Emitted when a component's health status changes."""

    component: str = ""
    status: str = ""  # "healthy", "degraded", "unhealthy"
    message: str = ""
