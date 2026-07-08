"""Tests for ComponentRegistry."""

import pytest

from orbit_core.exceptions.errors import CapabilityError
from orbit_core.registry.registry import ComponentRegistry


def test_registry_register_resolve() -> None:
    registry = ComponentRegistry()
    registry.register("db", {"conn": "sqlite"})
    
    val = registry.resolve("db")
    assert val == {"conn": "sqlite"}
    assert registry.has("db") is True


def test_registry_duplicate_raises() -> None:
    registry = ComponentRegistry()
    registry.register("db", 1)
    
    with pytest.raises(CapabilityError, match="Key already registered"):
        registry.register("db", 2)


def test_registry_missing_raises() -> None:
    registry = ComponentRegistry()
    with pytest.raises(CapabilityError, match="Key not found"):
        registry.resolve("nope")


def test_registry_list_all() -> None:
    registry = ComponentRegistry()
    registry.register("a", 1)
    registry.register("b", 2)
    
    assert set(registry.list_all()) == {"a", "b"}


def test_registry_unregister() -> None:
    registry = ComponentRegistry()
    registry.register("a", 1)
    registry.unregister("a")
    
    assert registry.has("a") is False
    assert registry.count == 0


def test_registry_clear() -> None:
    registry = ComponentRegistry()
    registry.register("a", 1)
    registry.clear()
    assert registry.count == 0
