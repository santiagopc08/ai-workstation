"""Tests for ORBIT Execution Sprint 1."""

import sys
from pathlib import Path

import pytest

from orbit_execution import (
    CancellationToken,
    ExecutionEngine,
    ExecutionOptions,
    ExecutionPolicy,
    ExecutionRequest,
    PolicyViolationError,
    ProcessState,
    TimeoutError,
)


@pytest.fixture
def engine() -> ExecutionEngine:
    return ExecutionEngine()


def test_execute_success(engine: ExecutionEngine) -> None:
    request = ExecutionRequest(
        command=[sys.executable, "-c", "print('hello orbit')"]
    )
    result = engine.execute(request)
    
    assert result.success is True
    assert result.process.exit_code == 0
    assert result.process.handle.state == ProcessState.EXITED
    assert result.process.stdout == b"hello orbit\n"
    assert result.process.stderr == b""


def test_execute_async(engine: ExecutionEngine) -> None:
    request = ExecutionRequest(
        command=[sys.executable, "-c", "import time; time.sleep(0.1); print('done')"]
    )
    handle = engine.execute_async(request)
    
    assert handle.id is not None
    assert handle.provider_id == "local"
    
    result = engine.wait(handle)
    
    assert result.success is True
    assert result.process.exit_code == 0
    assert result.process.handle.state == ProcessState.EXITED
    assert result.process.stdout == b"done\n"


def test_execute_failure(engine: ExecutionEngine) -> None:
    request = ExecutionRequest(
        command=[sys.executable, "-c", "import sys; sys.exit(42)"]
    )
    result = engine.execute(request)
    
    assert result.success is False
    assert result.process.exit_code == 42
    assert result.process.handle.state == ProcessState.FAILED
    assert result.error is not None


def test_timeout(engine: ExecutionEngine) -> None:
    request = ExecutionRequest(
        command=[sys.executable, "-c", "import time; time.sleep(10)"],
        policy=ExecutionPolicy(timeout_sec=0.1)
    )
    
    with pytest.raises(TimeoutError, match="timed out after 0.1s"):
        engine.execute(request)


def test_cancel(engine: ExecutionEngine) -> None:
    request = ExecutionRequest(
        command=[sys.executable, "-c", "import time; time.sleep(10)"]
    )
    handle = engine.execute_async(request)
    
    engine.cancel(handle, CancellationToken())
    
    # After cancellation, waiting should yield an ExecutionResult with a non-zero exit code
    # OR depending on OS, it might raise if we don't catch it, but our wait() just returns the exit code
    result = engine.wait(handle)
    assert result.success is False
    assert result.process.exit_code != 0
    assert result.process.handle.state == ProcessState.CANCELLED


def test_env_override(engine: ExecutionEngine) -> None:
    request = ExecutionRequest(
        command=[sys.executable, "-c", "import os; print(os.environ['ORBIT_TEST'])"],
        env={"ORBIT_TEST": "orbit_value"}
    )
    result = engine.execute(request)
    
    assert result.success is True
    assert result.process.stdout == b"orbit_value\n"


def test_cwd_override(engine: ExecutionEngine, tmp_path: Path) -> None:
    request = ExecutionRequest(
        command=[sys.executable, "-c", "import os; print(os.getcwd())"],
        cwd=str(tmp_path)
    )
    result = engine.execute(request)
    
    assert result.success is True
    # The output might have trailing path separators or newlines, so we check if tmp_path is in it
    assert str(tmp_path).encode("utf-8") in result.process.stdout


def test_stderr_merge(engine: ExecutionEngine) -> None:
    request = ExecutionRequest(
        command=[sys.executable, "-c", "import sys; sys.stderr.write('err'); sys.stdout.write('out')"],
        options=ExecutionOptions(merge_stderr=True)
    )
    result = engine.execute(request)
    
    assert result.success is True
    assert result.process.stderr == b""
    # Due to buffering, order of 'out' and 'err' might vary, but both should be in stdout
    assert b"err" in result.process.stdout
    assert b"out" in result.process.stdout


def test_empty_command(engine: ExecutionEngine) -> None:
    request = ExecutionRequest(command=[])
    
    with pytest.raises(PolicyViolationError, match="Command cannot be empty"):
        engine.execute(request)
