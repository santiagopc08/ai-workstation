"""Observability layer for ORBIT Execution."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from orbit_core.events.bus import EventBus
from orbit_core.interfaces.health import HealthCheck
from orbit_core.interfaces.logging import Logger
from orbit_core.interfaces.metrics import MetricsCollector
from orbit_core.types.models import HealthStatus

from orbit_execution.events import (
    ProcessCancelled,
    ProcessFailed,
    ProcessFinished,
    ProcessStarted,
    StderrChunk,
    StdoutChunk,
    TimeoutReached,
)

if TYPE_CHECKING:
    from orbit_execution.engine import ExecutionEngine


@dataclass
class ExecutionMetrics:
    """Telemetry payload for a single execution."""
    execution_id: str
    provider_id: str = "local"
    command: list[str] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    duration_ms: float = 0.0
    exit_code: int | None = None
    success: bool = False
    cancelled: bool = False
    timeout: bool = False
    policy_violations: int = 0
    stdout_bytes: int = 0
    stderr_bytes: int = 0


class InternalMetricsCollector(MetricsCollector):
    """In-memory aggregation of execution metrics."""

    def __init__(self) -> None:
        self.counters: dict[str, float] = {
            "total_executions": 0.0,
            "successful_executions": 0.0,
            "failed_executions": 0.0,
            "cancelled_executions": 0.0,
            "timeout_executions": 0.0,
            "policy_violations": 0.0,
        }
        self.durations: deque[float] = deque(maxlen=1000)

    def increment(self, name: str, value: float = 1.0) -> None:
        self.counters[name] = self.counters.get(name, 0.0) + value

    def gauge(self, name: str, value: float) -> None:
        self.counters[name] = value

    def timing(self, name: str, duration_ms: float) -> None:
        if name == "execution_duration_ms":
            self.durations.append(duration_ms)

    def get_average_duration(self) -> float:
        if not self.durations:
            return 0.0
        return sum(self.durations) / len(self.durations)

    def get_percentile(self, p: float) -> float:
        if not self.durations:
            return 0.0
        sorted_d = sorted(self.durations)
        k = (len(sorted_d) - 1) * p
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_d) else f
        if f == c:
            return sorted_d[f]
        d0 = sorted_d[f]
        d1 = sorted_d[c]
        return d0 + (d1 - d0) * (k - f)


class ExecutionTracer:
    """Listens to the EventBus to build ExecutionMetrics for each process."""

    def __init__(self, event_bus: EventBus, logger: Logger, metrics: MetricsCollector) -> None:
        self._event_bus = event_bus
        self._logger = logger
        self._metrics = metrics
        self._active_traces: dict[str, ExecutionMetrics] = {}

        self._event_bus.subscribe(ProcessStarted, self._on_started)
        self._event_bus.subscribe(ProcessFinished, self._on_finished)
        self._event_bus.subscribe(ProcessFailed, self._on_failed)
        self._event_bus.subscribe(ProcessCancelled, self._on_cancelled)
        self._event_bus.subscribe(TimeoutReached, self._on_timeout)
        self._event_bus.subscribe(StdoutChunk, self._on_stdout)
        self._event_bus.subscribe(StderrChunk, self._on_stderr)

    def _get_or_create(self, handle_id: str) -> ExecutionMetrics:
        if handle_id not in self._active_traces:
            self._active_traces[handle_id] = ExecutionMetrics(execution_id=handle_id)
        return self._active_traces[handle_id]

    def _on_started(self, event: ProcessStarted) -> None:
        trace = self._get_or_create(event.handle_id)
        trace.start_time = time.time()
        
        self._metrics.increment("total_executions")
        self._logger.info(f"Process started (pid={event.pid})", execution_id=event.handle_id)

    def _on_finished(self, event: ProcessFinished) -> None:
        trace = self._get_or_create(event.handle_id)
        trace.end_time = time.time()
        trace.duration_ms = (trace.end_time - trace.start_time) * 1000
        trace.exit_code = event.exit_code
        trace.success = True
        
        self._metrics.increment("successful_executions")
        self._metrics.timing("execution_duration_ms", trace.duration_ms)
        self._logger.info("Process finished successfully", execution_id=event.handle_id, duration_ms=trace.duration_ms)
        self._active_traces.pop(event.handle_id, None)

    def _on_failed(self, event: ProcessFailed) -> None:
        trace = self._get_or_create(event.handle_id)
        trace.end_time = time.time()
        trace.duration_ms = (trace.end_time - trace.start_time) * 1000
        # ProcessFailed currently just provides an error string
        trace.exit_code = -1
        
        self._metrics.increment("failed_executions")
        self._metrics.timing("execution_duration_ms", trace.duration_ms)
        self._logger.error(
            f"Process failed (error={event.error})",
            execution_id=event.handle_id,
            duration_ms=trace.duration_ms
        )
        self._active_traces.pop(event.handle_id, None)

    def _on_cancelled(self, event: ProcessCancelled) -> None:
        trace = self._get_or_create(event.handle_id)
        trace.end_time = time.time()
        trace.duration_ms = (trace.end_time - trace.start_time) * 1000
        trace.cancelled = True
        
        self._metrics.increment("cancelled_executions")
        self._metrics.timing("execution_duration_ms", trace.duration_ms)
        self._logger.warning(f"Process cancelled: {event.reason}", execution_id=event.handle_id, duration_ms=trace.duration_ms)
        self._active_traces.pop(event.handle_id, None)

    def _on_timeout(self, event: TimeoutReached) -> None:
        trace = self._get_or_create(event.handle_id)
        trace.timeout = True
        
        self._metrics.increment("timeout_executions")
        self._logger.error(f"Process timeout after {event.timeout_sec}s", execution_id=event.handle_id)

    def _on_stdout(self, event: StdoutChunk) -> None:
        trace = self._get_or_create(event.handle_id)
        trace.stdout_bytes += len(event.chunk)

    def _on_stderr(self, event: StderrChunk) -> None:
        trace = self._get_or_create(event.handle_id)
        trace.stderr_bytes += len(event.chunk)


class HealthReporter(HealthCheck):
    """Exposes ORBIT Execution engine health."""

    def __init__(self, engine: ExecutionEngine) -> None:
        import importlib.metadata
        self._engine = engine
        try:
            self._version = importlib.metadata.version("orbit-execution")
        except importlib.metadata.PackageNotFoundError:
            self._version = "unknown"
        self._start_time = time.time()

    def health(self) -> HealthStatus:
        uptime = time.time() - self._start_time
        
        active = len(self._engine._active_processes)
        
        # Pull from internal metrics if available
        completed = 0
        failed = 0
        if hasattr(self._engine, "metrics") and isinstance(self._engine.metrics, InternalMetricsCollector):
            completed = int(self._engine.metrics.counters.get("successful_executions", 0))
            failed = int(self._engine.metrics.counters.get("failed_executions", 0))

        dependencies = {
            "provider": self._engine._provider.__class__.__name__,
            "active_processes": str(active),
            "completed_processes": str(completed),
            "failed_processes": str(failed)
        }
        
        return HealthStatus(
            status="healthy",
            version=self._version,
            uptime=uptime,
            dependencies=dependencies
        )
