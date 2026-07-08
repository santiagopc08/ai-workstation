"""Tests for interfaces (structural typing)."""

from typing import Any

from orbit_core.interfaces.engine import Engine
from orbit_core.interfaces.health import HealthCheck
from orbit_core.interfaces.lifecycle import Lifecycle
from orbit_core.interfaces.providers import Provider
from orbit_core.types.models import HealthStatus


class MockComponent:
    @property
    def name(self) -> str:
        return "mock"

    @property
    def version(self) -> str:
        return "1.0"

    def initialize(self) -> None:
        pass

    def shutdown(self) -> None:
        pass

    def health(self) -> HealthStatus:
        return HealthStatus(status="healthy")


def test_structural_typing() -> None:
    comp: Any = MockComponent()

    assert isinstance(comp, Engine)
    assert isinstance(comp, Lifecycle)
    assert isinstance(comp, HealthCheck)
    assert isinstance(comp, Provider)
