"""Tests for Capability system."""

from orbit_core.capabilities.capability import Capability
from orbit_core.capabilities.plugin import Plugin


def test_capability_lifecycle() -> None:
    cap = Capability(id="test.db", name="DB", description="Test db", version="1.0")
    
    # Initial state
    assert cap.health().status == "stopped"
    
    # Init
    cap.initialize()
    assert cap.health().status == "healthy"
    
    # Shutdown
    cap.shutdown()
    assert cap.health().status == "stopped"


class MockPlugin:
    @property
    def id(self) -> str:
        return "mock"
        
    @property
    def name(self) -> str:
        return "Mock Plugin"
        
    @property
    def capabilities(self) -> list[Capability]:
        return [Capability(id="c1", name="C1", description="", version="1.0")]
        
    def register(self, registry: object) -> None:
        pass


def test_plugin_protocol() -> None:
    plugin: Plugin = MockPlugin()
    assert plugin.id == "mock"
    assert len(plugin.capabilities) == 1
