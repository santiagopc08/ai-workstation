from dataclasses import dataclass
from typing import Any, Callable, Type, TypeVar

T = TypeVar("T")

@dataclass(slots=True, frozen=True)
class DocumentCreated:
    path: str

@dataclass(slots=True, frozen=True)
class DocumentUpdated:
    path: str

@dataclass(slots=True, frozen=True)
class DocumentDeleted:
    path: str

@dataclass(slots=True, frozen=True)
class ChunkCreated:
    chunk_id: str
    document: str

@dataclass(slots=True, frozen=True)
class ChunkDeleted:
    chunk_id: str
    document: str

@dataclass(slots=True, frozen=True)
class EmbeddingCreated:
    chunk_id: str

@dataclass(slots=True, frozen=True)
class EmbeddingRemoved:
    chunk_id: str

@dataclass(slots=True, frozen=True)
class IndexFinished:
    stats: dict[str, Any]


class EventBus:
    """
    Bus de eventos en memoria y síncrono para comunicar la detección
    de cambios, creación de fragmentos y estado de indexación.
    """
    def __init__(self) -> None:
        self._listeners: dict[Type[Any], list[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: Type[T], callback: Callable[[T], None]) -> None:
        """Registra un receptor de eventos para un tipo específico de evento."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def publish(self, event: Any) -> None:
        """Emite un evento a todos los receptores interesados."""
        event_type = type(event)
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(event)
                except Exception:
                    # Evitar que fallos en un callback detengan el resto
                    continue

# Instancia global única del bus de eventos
event_bus: EventBus = EventBus()
