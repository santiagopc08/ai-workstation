"""Benchmarks for EventBus."""

from orbit_core.events.bus import EventBus
from orbit_core.events.types import Event
from orbit_core.utils.timing import Timer


def run():
    bus = EventBus()
    
    # 10 listeners
    for i in range(10):
        bus.subscribe(Event, lambda e: None)
        
    print(f"Running event bus benchmark (10 listeners, 100k events)...")
    
    with Timer() as t:
        for _ in range(100_000):
            bus.publish(Event())
            
    print(f"Elapsed: {t.elapsed_ms:.2f}ms")
    print(f"Events/sec: {100_000 / t.elapsed:.2f}")


if __name__ == "__main__":
    run()
