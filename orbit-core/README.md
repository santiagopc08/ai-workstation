# ORBIT Core

Shared contracts, types, and infrastructure for the ORBIT platform.

## What is ORBIT Core?

`orbit-core` is the foundational library that all other ORBIT engines depend on. It provides:
- A synchronous, lightweight **Event Bus** for decoupled inter-engine communication.
- A central **Component Registry** for engine discovery.
- Immutable **Shared Data Models** (using standard library `dataclass(frozen=True)`).
- Standardized **Structured Logging** (`OrbitLogger`).
- **Health Check** aggregators.

## Requirements

- **Python:** 3.10 or higher.
- **Package Manager:** `uv`

## Installation

```bash
uv sync
```

## First Use

```python
from orbit_core.events import EventBus, Event

# Initialize the bus
bus = EventBus()

# Subscribe to an event type
bus.subscribe(Event, lambda e: print(f"Received: {e.source}"))

# Publish an event
bus.publish(Event(source="docs"))
```

## Architecture Rules

- **Zero Dependencies:** `orbit-core` must absolutely NEVER depend on external third-party libraries (except for isolated, optional adapters like PyYAML).
- **No Asyncio:** The core event bus must remain strictly synchronous to ensure predictable, deterministic execution.
- **Immutable Types:** All shared models must use `dataclasses(frozen=True, slots=True)` to prevent unintended side effects across engine boundaries.
