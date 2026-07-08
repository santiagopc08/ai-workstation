# Examples

## Implementing a new ORBIT Engine

```python
from orbit_core.interfaces.engine import Engine
from orbit_core.types.models import HealthStatus
from orbit_core.providers.container import Container
from orbit_core.logging.logger import get_logger

logger = get_logger("orbit.my_engine")

class MyEngine:
    @property
    def name(self) -> str:
        return "MyEngine"
        
    @property
    def version(self) -> str:
        return "1.0.0"

    def initialize(self) -> None:
        logger.info("Starting engine")
        self.container = Container()
        
    def shutdown(self) -> None:
        logger.info("Stopping engine")
        self.container.clear()
        
    def health(self) -> HealthStatus:
        return HealthStatus(status="healthy", version=self.version)

# Usage
engine: Engine = MyEngine()
engine.initialize()
```

## Using the Event Bus

```python
from dataclasses import dataclass
from orbit_core.events.types import Event
from orbit_core.events.bus import EventBus

@dataclass(frozen=True)
class FileIndexed(Event):
    path: str
    
def on_file_indexed(event: FileIndexed) -> None:
    print(f"Indexed: {event.path}")
    
bus = EventBus()
bus.subscribe(FileIndexed, on_file_indexed)

# Later...
bus.publish(FileIndexed(path="/data/file.txt"))
```
