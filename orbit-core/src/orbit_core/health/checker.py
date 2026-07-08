"""Aggregated health checker for multiple components."""

from __future__ import annotations

import time
from typing import Any

from orbit_core.types.models import HealthStatus


class HealthChecker:
    """Aggregates multiple health checks and produces a consolidated report.

    Each registered check is a callable returning a HealthStatus.
    """

    def __init__(self) -> None:
        self._checks: dict[str, Any] = {}  # name -> HealthCheck protocol implementor
        self._start_time: float = time.monotonic()

    def register(self, name: str, check: Any) -> None:
        """Register a component that implements the HealthCheck protocol."""
        self._checks[name] = check

    def unregister(self, name: str) -> None:
        """Remove a registered health check."""
        self._checks.pop(name, None)

    def check_all(self) -> HealthStatus:
        """Execute all registered checks and consolidate into a single status."""
        dependencies: dict[str, str] = {}
        errors: list[str] = []
        overall = "healthy"

        for name, check in self._checks.items():
            try:
                status: HealthStatus = check.health()
                dependencies[name] = status.status
                if status.status != "healthy":
                    overall = "degraded"
                errors.extend(status.errors)
            except Exception as exc:  # noqa: BLE001
                dependencies[name] = "error"
                errors.append(f"{name}: {exc}")
                overall = "unhealthy"

        uptime = time.monotonic() - self._start_time
        return HealthStatus(
            status=overall,
            uptime=uptime,
            dependencies=dependencies,
            errors=errors,
        )

    @property
    def check_count(self) -> int:
        """Number of registered health checks."""
        return len(self._checks)
