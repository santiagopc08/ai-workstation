"""Tests for EventBus."""

from dataclasses import dataclass

from orbit_core.events.bus import EventBus
from orbit_core.events.types import Event, HealthChanged


@dataclass(frozen=True)
class CustomEvent(Event):
    value: int = 0


def test_event_bus_pub_sub() -> None:
    bus = EventBus()
    received = []

    def handler(evt: CustomEvent) -> None:
        received.append(evt.value)

    bus.subscribe(CustomEvent, handler)
    bus.publish(CustomEvent(value=42))

    assert len(received) == 1
    assert received[0] == 42
    assert bus.listener_count == 1


def test_event_bus_unsubscribe() -> None:
    bus = EventBus()
    received = []

    def handler(evt: CustomEvent) -> None:
        received.append(evt.value)

    bus.subscribe(CustomEvent, handler)
    bus.unsubscribe(CustomEvent, handler)
    bus.publish(CustomEvent(value=42))

    assert len(received) == 0
    assert bus.listener_count == 0


def test_event_bus_swallows_errors() -> None:
    bus = EventBus()
    received = []

    def bad_handler(evt: CustomEvent) -> None:
        raise ValueError("Boom")

    def good_handler(evt: CustomEvent) -> None:
        received.append(evt.value)

    bus.subscribe(CustomEvent, bad_handler)
    bus.subscribe(CustomEvent, good_handler)

    bus.publish(CustomEvent(value=10))
    assert len(received) == 1


def test_event_bus_clear() -> None:
    bus = EventBus()
    bus.subscribe(CustomEvent, lambda e: None)
    bus.clear()
    assert bus.listener_count == 0


def test_event_hierarchy_no_leak() -> None:
    bus = EventBus()
    received_health = []

    def health_handler(evt: HealthChanged) -> None:
        received_health.append(evt)

    bus.subscribe(HealthChanged, health_handler)
    bus.publish(Event())  # Base event
    bus.publish(HealthChanged(component="test", status="ok"))

    assert len(received_health) == 1
