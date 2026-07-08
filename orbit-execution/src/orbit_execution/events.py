"""Event models for ORBIT Execution Streaming."""

from __future__ import annotations

from dataclasses import dataclass

from orbit_core.events import Event


@dataclass(frozen=True, slots=True)
class StreamEvent(Event):
    """Base class for all execution stream events."""
    handle_id: str = ""


@dataclass(frozen=True, slots=True)
class StdoutChunk(StreamEvent):
    """A chunk of stdout from a running process."""
    chunk: bytes = b""


@dataclass(frozen=True, slots=True)
class StderrChunk(StreamEvent):
    """A chunk of stderr from a running process."""
    chunk: bytes = b""


@dataclass(frozen=True, slots=True)
class ProcessStarted(StreamEvent):
    """Emitted when a process successfully spawns."""
    pid: int = 0


@dataclass(frozen=True, slots=True)
class ProcessFinished(StreamEvent):
    """Emitted when a process exits naturally."""
    exit_code: int = 0


@dataclass(frozen=True, slots=True)
class ProcessFailed(StreamEvent):
    """Emitted when a process exits with a non-zero code or fails to spawn."""
    error: str = ""


@dataclass(frozen=True, slots=True)
class ProcessCancelled(StreamEvent):
    """Emitted when a process is cancelled."""
    reason: str = ""


@dataclass(frozen=True, slots=True)
class TimeoutReached(StreamEvent):
    """Emitted when a process exceeds its allowed execution time."""
    timeout_sec: float = 0.0
