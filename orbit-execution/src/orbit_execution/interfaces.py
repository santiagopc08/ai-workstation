"""Execution provider interface."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from orbit_execution.types import ProcessHandle, RunningProcess


@runtime_checkable
class ExecutionProvider(Protocol):
    """SPI for execution backends."""

    def spawn(self, handle: ProcessHandle) -> RunningProcess:
        """Spawn a new process for the given handle."""
        ...

    def kill(self, pid: int) -> None:
        """Immediately terminate the process with the given PID."""
        ...

    def wait(self, process: RunningProcess, timeout: float | None = None) -> int:
        """Wait for the process to exit and return its exit code."""
        ...
