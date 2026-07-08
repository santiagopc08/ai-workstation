"""Tests for ORBIT Execution Observability (RFC-007)."""

import sys
from typing import Any

import pytest

from orbit_execution import (
    ExecutionEngine,
    ExecutionPolicy,
    ExecutionRequest,
    InternalMetricsCollector,
)
from orbit_execution.exceptions import PolicyViolationError


def test_metrics_success() -> None:
    engine = ExecutionEngine()
    request = ExecutionRequest(command=[sys.executable, "-c", "print('hello')"])
    
    # Must be tracked
    result = engine.execute(request)
    assert result.success is True
    
    metrics = engine.metrics
    assert isinstance(metrics, InternalMetricsCollector)
    assert metrics.counters["total_executions"] == 1
    assert metrics.counters["successful_executions"] == 1
    assert metrics.counters["failed_executions"] == 0
    
    # Percentiles
    assert metrics.get_average_duration() > 0
    assert metrics.get_percentile(0.95) > 0


def test_metrics_failure() -> None:
    engine = ExecutionEngine()
    request = ExecutionRequest(command=[sys.executable, "-c", "import sys; sys.exit(1)"])
    
    result = engine.execute(request)
    assert result.success is False
    
    metrics = engine.metrics
    assert isinstance(metrics, InternalMetricsCollector)
    assert metrics.counters["total_executions"] == 1
    assert metrics.counters["failed_executions"] == 1


def test_metrics_policy_violation() -> None:
    engine = ExecutionEngine()
    
    request = ExecutionRequest(
        command=["rm", "-rf", "/"],
        policy=ExecutionPolicy(command_blacklist=["rm"])
    )
    
    with pytest.raises(PolicyViolationError):
        engine.execute(request)
        
    metrics = engine.metrics
    assert isinstance(metrics, InternalMetricsCollector)
    # The tracer didn't even start a process because it failed fast in execute_async
    assert metrics.counters.get("total_executions", 0) == 0
    assert metrics.counters["policy_violations"] == 1


def test_health_reporter() -> None:
    engine = ExecutionEngine()
    
    health = engine.health_reporter.health()
    assert health.status == "healthy"
    assert "version" in health.version or health.version != ""
    assert health.uptime >= 0
    assert health.dependencies["provider"] == "LocalExecutionProvider"
    assert health.dependencies["active_processes"] == "0"
    assert health.dependencies["completed_processes"] == "0"


def test_custom_logger_receives_traces() -> None:
    class MockLogger:
        def __init__(self) -> None:
            self.logs: list[tuple[str, str, dict[str, Any]]] = []
            
        def info(self, msg: str, **kwargs: Any) -> None:
            self.logs.append(("INFO", msg, kwargs))
            
        def error(self, msg: str, **kwargs: Any) -> None:
            self.logs.append(("ERROR", msg, kwargs))
            
        def warning(self, msg: str, **kwargs: Any) -> None:
            self.logs.append(("WARNING", msg, kwargs))

    logger = MockLogger()
    # Cast to ignore structural mismatches for unused methods
    engine = ExecutionEngine(logger=logger)  # type: ignore
    
    request = ExecutionRequest(command=[sys.executable, "-c", "print(1)"])
    result = engine.execute(request)
    
    assert len(logger.logs) >= 2
    # Ensure execution_id was injected
    assert "execution_id" in logger.logs[0][2]
    assert logger.logs[0][2]["execution_id"] == result.process.handle.id
