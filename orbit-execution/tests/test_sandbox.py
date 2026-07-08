"""Tests for ORBIT Execution Sandboxing (RFC-008)."""

import os
import shutil
import sys
from pathlib import Path

import pytest

from orbit_execution import ExecutionEngine, ExecutionPolicy, ExecutionRequest, SandboxViolationError


def test_sandbox_cwd_does_not_exist() -> None:
    engine = ExecutionEngine()
    request = ExecutionRequest(
        command=[sys.executable, "-c", "print(1)"],
        cwd="/path/to/nonexistent_8237498234"
    )
    with pytest.raises(SandboxViolationError, match="CWD does not exist"):
        engine.execute(request)


def test_sandbox_executable_not_found() -> None:
    engine = ExecutionEngine()
    request = ExecutionRequest(
        command=["nonexistent_executable_12345"]
    )
    with pytest.raises(SandboxViolationError, match="Executable not found"):
        engine.execute(request)


def test_sandbox_lacks_permissions(tmp_path: Path) -> None:
    # Create a fake executable file without execute permissions
    fake_exe = tmp_path / "fake_binary"
    fake_exe.write_text("#!/bin/sh\necho 'hello'")
    # Explicitly remove execute permissions
    os.chmod(fake_exe, 0o644)
    
    engine = ExecutionEngine()
    request = ExecutionRequest(
        command=[str(fake_exe)]
    )
    with pytest.raises(SandboxViolationError, match="lacks execute permissions"):
        engine.execute(request)


def test_sandbox_path_traversal_cwd(tmp_path: Path) -> None:
    sandbox_dir = tmp_path / "sandbox"
    sandbox_dir.mkdir()
    
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    
    engine = ExecutionEngine(
        global_policy=ExecutionPolicy(allowed_cwds=[str(sandbox_dir)])
    )
    
    # Create a symlink inside the sandbox pointing to the outside
    symlink_cwd = sandbox_dir / "sneaky_link"
    os.symlink(str(outside_dir), str(symlink_cwd))
    
    request = ExecutionRequest(
        command=[sys.executable, "-c", "print(1)"],
        cwd=str(symlink_cwd)
    )
    
    with pytest.raises(SandboxViolationError, match="escape detected for CWD"):
        engine.execute(request)


def test_sandbox_shell_bypass_via_symlink(tmp_path: Path) -> None:
    # Simulates an attacker symlinking 'bash' to 'my_safe_app' to bypass allow_shell=False
    bash_path = shutil.which("bash") or shutil.which("sh")
    if not bash_path:
        pytest.skip("No shell available for test")
        
    safe_link = tmp_path / "my_safe_app"
    os.symlink(bash_path, safe_link)
    
    engine = ExecutionEngine(
        global_policy=ExecutionPolicy(allow_shell=False)
    )
    
    request = ExecutionRequest(
        command=[str(safe_link), "-c", "echo 'pwned'"]
    )
    
    with pytest.raises(SandboxViolationError, match="Shell execution bypassed"):
        engine.execute(request)


def test_sandbox_success() -> None:
    engine = ExecutionEngine()
    request = ExecutionRequest(
        command=[sys.executable, "-c", "print('safe')"]
    )
    result = engine.execute(request)
    assert result.success is True
