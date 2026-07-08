"""Tests for ORBIT Execution Streaming (RFC-005)."""

import sys
from typing import Any

import pytest
from orbit_core.events.bus import EventBus

from orbit_execution import (
    CancellationToken,
    ExecutionEngine,
    ExecutionOptions,
    ExecutionPolicy,
    ExecutionRequest,
    ProcessCancelled,
    ProcessFailed,
    ProcessFinished,
    ProcessStarted,
    StderrChunk,
    StdoutChunk,
    TimeoutError,
    TimeoutReached,
)


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def engine(event_bus: EventBus) -> ExecutionEngine:
    return ExecutionEngine(event_bus=event_bus)


def test_streaming_stdout_and_stderr(engine: ExecutionEngine, event_bus: EventBus) -> None:
    events: list[Any] = []
    
    def on_stdout(e: StdoutChunk) -> None:
        events.append(("out", e.chunk))
        
    def on_stderr(e: StderrChunk) -> None:
        events.append(("err", e.chunk))
        
    def on_started(e: ProcessStarted) -> None:
        events.append(("started", e.pid))

    def on_finished(e: ProcessFinished) -> None:
        events.append(("finished", e.exit_code))

    event_bus.subscribe(StdoutChunk, on_stdout)
    event_bus.subscribe(StderrChunk, on_stderr)
    event_bus.subscribe(ProcessStarted, on_started)
    event_bus.subscribe(ProcessFinished, on_finished)

    code = """
import sys
import time
sys.stdout.write('out1')
sys.stdout.flush()
sys.stderr.write('err1')
sys.stderr.flush()
"""
    request = ExecutionRequest(
        command=[sys.executable, "-c", code],
        options=ExecutionOptions(publish_streams=True)
    )
    result = engine.execute(request)
    
    assert result.success is True
    
    # Check events
    event_types = [e[0] for e in events]
    assert "started" in event_types
    assert "finished" in event_types
    assert ("out", b"out1") in events
    assert ("err", b"err1") in events


def test_silent_process(engine: ExecutionEngine, event_bus: EventBus) -> None:
    events: list[Any] = []
    event_bus.subscribe(StdoutChunk, lambda e: events.append("out"))
    event_bus.subscribe(StderrChunk, lambda e: events.append("err"))
    event_bus.subscribe(ProcessFinished, lambda e: events.append("finished"))

    request = ExecutionRequest(
        command=[sys.executable, "-c", "pass"],
        options=ExecutionOptions(publish_streams=True)
    )
    engine.execute(request)
    
    assert "out" not in events
    assert "err" not in events
    assert "finished" in events


def test_timeout_emits_event(engine: ExecutionEngine, event_bus: EventBus) -> None:
    events: list[Any] = []
    event_bus.subscribe(TimeoutReached, lambda e: events.append(e))

    request = ExecutionRequest(
        command=[sys.executable, "-c", "import time; time.sleep(10)"],
        policy=ExecutionPolicy(timeout_sec=0.1)
    )
    
    with pytest.raises(TimeoutError):
        engine.execute(request)
        
    assert any(isinstance(e, TimeoutReached) for e in events)


def test_cancel_emits_event(engine: ExecutionEngine, event_bus: EventBus) -> None:
    events: list[Any] = []
    event_bus.subscribe(ProcessCancelled, lambda e: events.append(e))

    request = ExecutionRequest(
        command=[sys.executable, "-c", "import time; time.sleep(10)"]
    )
    handle = engine.execute_async(request)
    engine.cancel(handle, CancellationToken())
    
    engine.wait(handle)
    
    assert any(isinstance(e, ProcessCancelled) for e in events)


def test_failure_emits_event(engine: ExecutionEngine, event_bus: EventBus) -> None:
    events: list[Any] = []
    event_bus.subscribe(ProcessFailed, lambda e: events.append(e))

    request = ExecutionRequest(
        command=[sys.executable, "-c", "import sys; sys.exit(42)"]
    )
    engine.execute(request)
    
    assert any(isinstance(e, ProcessFailed) for e in events)


def test_streams_without_publish_flag(engine: ExecutionEngine, event_bus: EventBus) -> None:
    events: list[Any] = []
    event_bus.subscribe(StdoutChunk, lambda e: events.append(e))

    request = ExecutionRequest(
        command=[sys.executable, "-c", "print('hello')"],
        options=ExecutionOptions(publish_streams=False)
    )
    result = engine.execute(request)
    
    # We still get stdout in the result
    assert result.process.stdout == b"hello\n"
    # But it wasn't published on the bus
    assert len(events) == 0
