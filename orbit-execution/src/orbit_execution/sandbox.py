"""OS-level Sandboxing for ORBIT Execution."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass

from orbit_execution.exceptions import SandboxViolationError
from orbit_execution.types import ExecutionPolicy, ExecutionRequest


@dataclass
class SandboxPolicy:
    """Physical constraints distilled from ExecutionPolicy."""
    allowed_cwds: list[str] | None = None
    blocked_cwds: list[str] | None = None
    allow_shell: bool | None = None


class SandboxValidator:
    """Performs deep OS-level validation of execution bounds."""

    def validate(self, request: ExecutionRequest, policy: SandboxPolicy) -> None:
        """Validate execution bounds physically on the OS."""
        self._validate_cwd(request, policy)
        self._validate_executable(request, policy)

    def _validate_cwd(self, request: ExecutionRequest, policy: SandboxPolicy) -> None:
        cwd = request.cwd or os.getcwd()
        
        # 1. Existence and Type
        if not os.path.exists(cwd):
            raise SandboxViolationError(f"CWD does not exist: {cwd}")
        if not os.path.isdir(cwd):
            raise SandboxViolationError(f"CWD is not a directory: {cwd}")
            
        # 2. Symlink & Traversal resolution
        real_cwd = os.path.realpath(cwd)
        
        if policy.allowed_cwds is not None:
            allowed = False
            for acwd in policy.allowed_cwds:
                real_acwd = os.path.realpath(acwd)
                if real_cwd == real_acwd or real_cwd.startswith(real_acwd + os.sep):
                    allowed = True
                    break
            if not allowed:
                raise SandboxViolationError(f"Symlink/Traversal escape detected for CWD: {real_cwd}")
                
        if policy.blocked_cwds is not None:
            for bcwd in policy.blocked_cwds:
                real_bcwd = os.path.realpath(bcwd)
                if real_cwd == real_bcwd or real_cwd.startswith(real_bcwd + os.sep):
                    raise SandboxViolationError(f"CWD resolved to a blocked path: {real_cwd}")

    def _validate_executable(self, request: ExecutionRequest, policy: SandboxPolicy) -> None:
        if not request.command:
            return  # Caught by PolicyManager earlier
            
        exe = request.command[0]
        
        # 1. Resolution
        exe_path = shutil.which(exe)
        if not exe_path:
            if os.path.exists(exe) and not os.access(exe, os.X_OK):
                raise SandboxViolationError(f"Executable lacks execute permissions: {exe}")
            raise SandboxViolationError(f"Executable not found in PATH: {exe}")
            
        # 2. Symlink resolution
        real_exe = os.path.realpath(exe_path)
        
        # 3. Execution permissions
        if not os.access(real_exe, os.X_OK):
            raise SandboxViolationError(f"Executable lacks execute permissions: {real_exe}")
            
        # 4. Shell bypass via symlinks
        if policy.allow_shell is False:
            base_name = os.path.basename(real_exe)
            if base_name in ("sh", "bash", "zsh", "cmd", "powershell", "pwsh"):
                raise SandboxViolationError(f"Shell execution bypassed via symlink/path: {real_exe}")


class SandboxManager:
    """Facade for applying physical OS sandboxing."""

    def __init__(self) -> None:
        self.validator = SandboxValidator()

    def enforce(self, request: ExecutionRequest, policy: ExecutionPolicy) -> None:
        """Enforce physical boundaries derived from the ExecutionPolicy."""
        sandbox_policy = SandboxPolicy(
            allowed_cwds=policy.allowed_cwds,
            blocked_cwds=policy.blocked_cwds,
            allow_shell=policy.allow_shell
        )
        self.validator.validate(request, sandbox_policy)
