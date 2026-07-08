"""Public types and models for ORBIT Execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProcessState(Enum):
    """Lifecycle states of a process."""
    CREATED = "CREATED"
    VALIDATED = "VALIDATED"
    SPAWNING = "SPAWNING"
    RUNNING = "RUNNING"
    EXITED = "EXITED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    TIMEOUT = "TIMEOUT"


@dataclass(frozen=True, slots=True)
class ExecutionOptions:
    """Modifiers for execution behavior."""
    merge_stderr: bool = False
    encoding: str = "utf-8"
    publish_streams: bool = False


@dataclass(frozen=True, slots=True)
class ExecutionPolicy:
    """Security and bounding constraints."""
    timeout_sec: float | None = None
    max_memory_mb: int | None = None
    allowed_cwds: list[str] | None = None
    blocked_cwds: list[str] | None = None
    env_whitelist: list[str] | None = None
    env_blacklist: list[str] | None = None
    command_whitelist: list[str] | None = None
    command_blacklist: list[str] | None = None
    interactive_allowed: bool | None = None
    allow_shell: bool | None = None


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    """The intent to execute a process."""
    command: list[str]
    cwd: str | None = None
    env: dict[str, str] = field(default_factory=dict)
    options: ExecutionOptions = field(default_factory=ExecutionOptions)
    policy: ExecutionPolicy | None = None


@dataclass(frozen=True, slots=True)
class ProcessHandle:
    """Opaque reference to an execution request."""
    id: str
    provider_id: str
    request: ExecutionRequest
    state: ProcessState = ProcessState.CREATED


@dataclass(frozen=True, slots=True)
class CancellationToken:
    """Signal payload for cooperative or aggressive cancellation."""
    reason: str = "Cancelled by user"
    force_kill: bool = False


@dataclass(frozen=True)
class RunningProcess:
    """Live interface to a spawned process."""
    handle: ProcessHandle
    pid: int
    start_time: float
    _internal_process: Any = field(repr=False, compare=False)
    
    def send_stdin(self, data: bytes) -> None:
        """Send data to the standard input of the process."""
        raise NotImplementedError("Streaming is not implemented in Sprint 1")


@dataclass(frozen=True, slots=True)
class CompletedProcess:
    """Terminal state of an executed process."""
    handle: ProcessHandle
    exit_code: int
    stdout: bytes
    stderr: bytes
    duration_ms: int


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    """Final payload returned to the caller."""
    success: bool
    process: CompletedProcess
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
