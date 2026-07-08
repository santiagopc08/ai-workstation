"""Tests for DI Container."""

import pytest

from orbit_core.exceptions.errors import ProviderError
from orbit_core.providers.container import Container


class DummyInterface:
    pass


class DummyImpl(DummyInterface):
    pass


def test_container_instance() -> None:
    container = Container()
    impl = DummyImpl()
    
    container.register_instance(DummyInterface, impl)
    
    assert container.has(DummyInterface) is True
    assert container.resolve(DummyInterface) is impl


def test_container_factory() -> None:
    container = Container()
    calls = 0
    
    def factory() -> DummyInterface:
        nonlocal calls
        calls += 1
        return DummyImpl()
        
    container.register_factory(DummyInterface, factory)
    
    # First resolve calls factory
    res1 = container.resolve(DummyInterface)
    assert calls == 1
    
    # Second resolve uses cached instance
    res2 = container.resolve(DummyInterface)
    assert calls == 1
    
    assert res1 is res2


def test_container_missing_raises() -> None:
    container = Container()
    with pytest.raises(ProviderError, match="No registration for"):
        container.resolve(DummyInterface)


def test_container_clear() -> None:
    container = Container()
    container.register_instance(DummyInterface, DummyImpl())
    container.clear()
    assert container.has(DummyInterface) is False
