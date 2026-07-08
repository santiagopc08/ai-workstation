"""Metrics collector protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class MetricsCollector(Protocol):
    """Observability metrics contract."""

    def increment(self, name: str, value: float = 1.0) -> None: ...
    def gauge(self, name: str, value: float) -> None: ...
    def timing(self, name: str, duration_ms: float) -> None: ...
