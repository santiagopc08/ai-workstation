"""ORBIT Execution Engine."""

from __future__ import annotations

import os
import signal
import subprocess
import threading
import time
import uuid
from typing import IO

from orbit_core.events.bus import EventBus
from orbit_core.interfaces.logging import Logger
from orbit_core.interfaces.metrics import MetricsCollector
from orbit_core.registry.registry import ComponentRegistry

from orbit_execution.events import (
    ProcessCancelled,
    ProcessFailed,
    ProcessFinished,
    ProcessStarted,
    StderrChunk,
    StdoutChunk,
    TimeoutReached,
)
from orbit_execution.exceptions import PolicyViolationError, SandboxViolationError, TimeoutError
from orbit_execution.observability import ExecutionTracer, HealthReporter, InternalMetricsCollector
from orbit_execution.policies import PolicyManager
from orbit_execution.providers.local import LocalExecutionProvider
from orbit_execution.sandbox import SandboxManager
from orbit_execution.types import (
    CancellationToken,
    CompletedProcess,
    ExecutionPolicy,
    ExecutionRequest,
    ExecutionResult,
    ProcessHandle,
    ProcessState,
    RunningProcess,
)


class ExecutionEngine:
    """Main entry point for ORBIT Execution."""

    def __init__(
        self,
        global_policy: ExecutionPolicy | None = None,
        event_bus: EventBus | None = None,
        logger: Logger | None = None,
        metrics: MetricsCollector | None = None,
        registry: ComponentRegistry | None = None
    ) -> None:
        """Initialize the execution engine."""
        from orbit_core.logging.logger import get_logger
        
        self._global_policy = global_policy
        self._event_bus = event_bus or EventBus()
        self.logger = logger or get_logger("execution")
        self.metrics = metrics or InternalMetricsCollector()
        
        self.tracer = ExecutionTracer(self._event_bus, self.logger, self.metrics)
        self.health_reporter = HealthReporter(self)
        if registry:
            registry.register("health.execution", self.health_reporter)
            
        self._provider = LocalExecutionProvider()
        self._active_processes: dict[str, RunningProcess] = {}
        self._cancelled_processes: set[str] = set()
        self._policy_manager = PolicyManager()
        self._sandbox_manager = SandboxManager()
        
        # Maps handle_id to (stdout_thread, stderr_thread, stdout_buf, stderr_buf)
        self._stream_readers: dict[str, tuple[threading.Thread | None, threading.Thread | None, bytearray, bytearray]] = {}

    def _read_stream(self, stream: IO[bytes] | None, buf: bytearray, handle_id: str, is_stderr: bool, publish: bool) -> None:
        """Read from a stream continuously, buffer it, and optionally publish chunks."""
        if not stream:
            return
            
        try:
            while True:
                # Read in chunks to remain responsive and avoid massive memory spikes
                chunk = stream.read(4096)
                if not chunk:
                    break
                    
                buf.extend(chunk)
                
                if publish:
                    if is_stderr:
                        self._event_bus.publish(StderrChunk(handle_id=handle_id, chunk=chunk))
                    else:
                        self._event_bus.publish(StdoutChunk(handle_id=handle_id, chunk=chunk))
        except (ValueError, OSError):
            # Stream closed or IO error, normal during teardown
            pass

    def execute_async(self, request: ExecutionRequest) -> ProcessHandle:
        """Submit an execution request asynchronously."""
        try:
            policy = self._policy_manager.resolve_and_validate(request, None, self._global_policy)
            self._sandbox_manager.enforce(request, policy)
        except (PolicyViolationError, SandboxViolationError) as e:
            if isinstance(self.metrics, InternalMetricsCollector):
                self.metrics.increment("policy_violations")
            self.logger.error(f"Policy/Sandbox violation: {str(e)}")
            raise
            
        merged_request = ExecutionRequest(
            command=request.command,
            cwd=request.cwd,
            env=request.env,
            options=request.options,
            policy=policy
        )

        handle = ProcessHandle(
            id=str(uuid.uuid4()),
            provider_id="local",
            request=merged_request,
            state=ProcessState.SPAWNING
        )

        process = self._provider.spawn(handle)
        self._active_processes[handle.id] = process
        
        self._event_bus.publish(ProcessStarted(handle_id=handle.id, pid=process.pid))
        
        # Setup streaming threads
        publish = request.options.publish_streams
        stdout_buf = bytearray()
        stderr_buf = bytearray()
        
        internal: subprocess.Popen[bytes] = process._internal_process
        t_out = None
        t_err = None
        
        if internal.stdout:
            t_out = threading.Thread(
                target=self._read_stream,
                args=(internal.stdout, stdout_buf, handle.id, False, publish),
                daemon=True,
                name=f"orbit-exec-stdout-{handle.id}"
            )
            t_out.start()
            
        if internal.stderr:
            t_err = threading.Thread(
                target=self._read_stream,
                args=(internal.stderr, stderr_buf, handle.id, True, publish),
                daemon=True,
                name=f"orbit-exec-stderr-{handle.id}"
            )
            t_err.start()
            
        self._stream_readers[handle.id] = (t_out, t_err, stdout_buf, stderr_buf)

        return ProcessHandle(
            id=handle.id,
            provider_id=handle.provider_id,
            request=handle.request,
            state=ProcessState.RUNNING
        )

    def wait(self, handle: ProcessHandle) -> ExecutionResult:
        """Wait for a process to complete."""
        if handle.id not in self._active_processes:
            raise ValueError(f"Process {handle.id} is not running or unknown")

        process = self._active_processes[handle.id]
        timeout_sec = handle.request.policy.timeout_sec if handle.request.policy else None
        start_time = process.start_time

        try:
            exit_code = self._provider.wait(process, timeout=timeout_sec)
        except subprocess.TimeoutExpired as e:
            self._event_bus.publish(TimeoutReached(handle_id=handle.id, timeout_sec=timeout_sec or 0.0))
            self.cancel(handle, CancellationToken(reason="Timeout", force_kill=True))
            self._cancelled_processes.discard(handle.id)
            del self._active_processes[handle.id]
            # Also cleanup stream readers if we raise early
            self._cleanup_readers(handle.id)
            raise TimeoutError(f"Process {handle.id} timed out after {timeout_sec}s") from e

        # Wait for stream readers to finish
        t_out, t_err, stdout_buf, stderr_buf = self._stream_readers[handle.id]
        if t_out:
            t_out.join(timeout=2.0)
        if t_err:
            t_err.join(timeout=2.0)

        duration_ms = int((time.time() - start_time) * 1000)
        
        # Determine final state
        if handle.id in self._cancelled_processes:
            final_state = ProcessState.CANCELLED
            self._event_bus.publish(ProcessCancelled(handle_id=handle.id, reason="User cancellation"))
            self._cancelled_processes.remove(handle.id)
        elif exit_code == 0:
            final_state = ProcessState.EXITED
            self._event_bus.publish(ProcessFinished(handle_id=handle.id, exit_code=0))
        else:
            final_state = ProcessState.FAILED
            self._event_bus.publish(ProcessFailed(handle_id=handle.id, error=f"Exit code {exit_code}"))
        
        completed = CompletedProcess(
            handle=ProcessHandle(
                id=handle.id, 
                provider_id=handle.provider_id, 
                request=handle.request, 
                state=final_state
            ),
            exit_code=exit_code,
            stdout=bytes(stdout_buf),
            stderr=bytes(stderr_buf),
            duration_ms=duration_ms
        )

        del self._active_processes[handle.id]
        self._cleanup_readers(handle.id)

        return ExecutionResult(
            success=(exit_code == 0),
            process=completed,
            error=None if exit_code == 0 else f"Process exited with code {exit_code}"
        )
        
    def _cleanup_readers(self, handle_id: str) -> None:
        """Remove stream reader references to allow garbage collection."""
        self._stream_readers.pop(handle_id, None)

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Execute a process synchronously."""
        handle = self.execute_async(request)
        return self.wait(handle)

    def cancel(self, handle: ProcessHandle, token: CancellationToken) -> None:
        """Cancel a running process."""
        if handle.id not in self._active_processes:
            return

        process = self._active_processes[handle.id]
        self._cancelled_processes.add(handle.id)
        
        if token.force_kill:
            self._provider.kill(process.pid)
        else:
            try:
                if os.name == "nt":
                    self._provider.kill(process.pid)
                else:
                    os.kill(process.pid, signal.SIGTERM)
            except OSError:
                pass
