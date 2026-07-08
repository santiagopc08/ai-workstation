"""Tests for ORBIT Execution Policies (RFC-006)."""

import os
import sys

import pytest

from orbit_execution import (
    ExecutionEngine,
    ExecutionPolicy,
    ExecutionRequest,
    PolicyViolationError,
)
from orbit_execution.policies import PolicyManager


def test_command_cannot_be_empty() -> None:
    engine = ExecutionEngine()
    request = ExecutionRequest(command=[])
    
    with pytest.raises(PolicyViolationError, match="Command cannot be empty"):
        engine.execute(request)


def test_command_whitelist() -> None:
    engine = ExecutionEngine(global_policy=ExecutionPolicy(command_whitelist=[sys.executable]))
    
    # Allowed
    request = ExecutionRequest(command=[sys.executable, "-c", "print(1)"])
    result = engine.execute(request)
    assert result.success is True
    
    # Blocked
    bad_request = ExecutionRequest(command=["ls", "-la"])
    with pytest.raises(PolicyViolationError, match="not in the whitelist"):
        engine.execute(bad_request)


def test_command_blacklist() -> None:
    engine = ExecutionEngine(global_policy=ExecutionPolicy(command_blacklist=["rm", "sudo"]))
    
    request = ExecutionRequest(command=["rm", "-rf", "/tmp/fake"])
    with pytest.raises(PolicyViolationError, match="is blacklisted"):
        engine.execute(request)


def test_cwd_allowed() -> None:
    cwd = os.getcwd()
    engine = ExecutionEngine(global_policy=ExecutionPolicy(allowed_cwds=[cwd]))
    
    # Current directory should be allowed
    request = ExecutionRequest(command=[sys.executable, "-c", "print(1)"], cwd=cwd)
    result = engine.execute(request)
    assert result.success is True
    
    # Root directory should be blocked
    bad_request = ExecutionRequest(command=[sys.executable, "-c", "print(1)"], cwd="/")
    with pytest.raises(PolicyViolationError, match="not within any allowed paths"):
        engine.execute(bad_request)


def test_cwd_blocked() -> None:
    engine = ExecutionEngine(global_policy=ExecutionPolicy(blocked_cwds=["/tmp"]))
    
    # /tmp is blocked
    bad_request = ExecutionRequest(command=[sys.executable, "-c", "print(1)"], cwd="/tmp")
    with pytest.raises(PolicyViolationError, match="within a blocked path"):
        engine.execute(bad_request)


def test_env_whitelist() -> None:
    engine = ExecutionEngine(global_policy=ExecutionPolicy(env_whitelist=["FOO"]))
    
    # FOO is allowed
    request = ExecutionRequest(command=[sys.executable, "-c", "print(1)"], env={"FOO": "bar"})
    engine.execute(request)
    
    # BAZ is not allowed
    bad_request = ExecutionRequest(command=[sys.executable, "-c", "print(1)"], env={"BAZ": "qux"})
    with pytest.raises(PolicyViolationError, match="not in the whitelist"):
        engine.execute(bad_request)


def test_env_blacklist() -> None:
    engine = ExecutionEngine(global_policy=ExecutionPolicy(env_blacklist=["AWS_SECRET"]))
    
    bad_request = ExecutionRequest(command=[sys.executable, "-c", "print(1)"], env={"AWS_SECRET": "123"})
    with pytest.raises(PolicyViolationError, match="is blacklisted"):
        engine.execute(bad_request)


def test_allow_shell() -> None:
    engine = ExecutionEngine(global_policy=ExecutionPolicy(allow_shell=False))
    
    bad_request = ExecutionRequest(command=["bash", "-c", "echo hello"])
    with pytest.raises(PolicyViolationError, match="Shell execution is not allowed"):
        engine.execute(bad_request)


def test_policy_inheritance() -> None:
    # Global blocks shell
    engine = ExecutionEngine(global_policy=ExecutionPolicy(allow_shell=False, timeout_sec=10))
    
    # Request overrides allow_shell to True
    # In fallback inheritance (Request -> Engine -> Global), if Request specifies allow_shell=True, it wins.
    request = ExecutionRequest(
        command=["bash", "-c", "echo hello"],
        policy=ExecutionPolicy(allow_shell=True)
    )
    
    pm = PolicyManager()
    resolved = pm.resolve_and_validate(request, None, engine._global_policy)
    
    assert resolved.allow_shell is True
    assert resolved.timeout_sec == 10  # Inherited from global


def test_multiple_violations_fails_fast() -> None:
    engine = ExecutionEngine(
        global_policy=ExecutionPolicy(
            command_blacklist=["rm"],
            blocked_cwds=["/tmp"]
        )
    )
    
    # Uses blocked command AND blocked cwd. Command is validated first typically.
    request = ExecutionRequest(command=["rm", "-rf"], cwd="/tmp")
    with pytest.raises(PolicyViolationError):
        engine.execute(request)
