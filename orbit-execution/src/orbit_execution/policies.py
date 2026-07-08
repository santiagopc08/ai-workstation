"""Policy engine for ORBIT Execution."""

from __future__ import annotations

import os

from orbit_execution.exceptions import PolicyViolationError
from orbit_execution.types import ExecutionPolicy, ExecutionRequest


class PolicyResolver:
    """Resolves policy inheritance (Request > Engine > Global)."""

    def resolve(
        self,
        request_policy: ExecutionPolicy | None,
        engine_policy: ExecutionPolicy | None,
        global_policy: ExecutionPolicy | None
    ) -> ExecutionPolicy:
        """Merge policies using fallback logic: Request wins over Engine wins over Global."""
        from typing import Any
        
        def fallback(*values: Any) -> Any:
            for v in values:
                if v is not None:
                    return v
            return None

        return ExecutionPolicy(
            timeout_sec=fallback(
                getattr(request_policy, "timeout_sec", None),
                getattr(engine_policy, "timeout_sec", None),
                getattr(global_policy, "timeout_sec", None),
            ),
            max_memory_mb=fallback(
                getattr(request_policy, "max_memory_mb", None),
                getattr(engine_policy, "max_memory_mb", None),
                getattr(global_policy, "max_memory_mb", None),
            ),
            allowed_cwds=fallback(
                getattr(request_policy, "allowed_cwds", None),
                getattr(engine_policy, "allowed_cwds", None),
                getattr(global_policy, "allowed_cwds", None),
            ),
            blocked_cwds=fallback(
                getattr(request_policy, "blocked_cwds", None),
                getattr(engine_policy, "blocked_cwds", None),
                getattr(global_policy, "blocked_cwds", None),
            ),
            env_whitelist=fallback(
                getattr(request_policy, "env_whitelist", None),
                getattr(engine_policy, "env_whitelist", None),
                getattr(global_policy, "env_whitelist", None),
            ),
            env_blacklist=fallback(
                getattr(request_policy, "env_blacklist", None),
                getattr(engine_policy, "env_blacklist", None),
                getattr(global_policy, "env_blacklist", None),
            ),
            command_whitelist=fallback(
                getattr(request_policy, "command_whitelist", None),
                getattr(engine_policy, "command_whitelist", None),
                getattr(global_policy, "command_whitelist", None),
            ),
            command_blacklist=fallback(
                getattr(request_policy, "command_blacklist", None),
                getattr(engine_policy, "command_blacklist", None),
                getattr(global_policy, "command_blacklist", None),
            ),
            interactive_allowed=fallback(
                getattr(request_policy, "interactive_allowed", None),
                getattr(engine_policy, "interactive_allowed", None),
                getattr(global_policy, "interactive_allowed", None),
            ),
            allow_shell=fallback(
                getattr(request_policy, "allow_shell", None),
                getattr(engine_policy, "allow_shell", None),
                getattr(global_policy, "allow_shell", None),
            )
        )


class PolicyValidator:
    """Validates an ExecutionRequest against a resolved ExecutionPolicy."""

    def validate(self, request: ExecutionRequest, policy: ExecutionPolicy) -> None:
        """Validate request and raise PolicyViolationError if constraints are breached."""
        if not request.command:
            raise PolicyViolationError("Command cannot be empty")

        # 1. Shell Validation
        base_cmd = request.command[0]
        if policy.allow_shell is False and base_cmd in ("sh", "bash", "zsh", "cmd", "powershell", "pwsh"):
            raise PolicyViolationError(f"Shell execution is not allowed, blocked: {base_cmd}")

        # 2. Command whitelist/blacklist
        if policy.command_whitelist is not None and base_cmd not in policy.command_whitelist:
            raise PolicyViolationError(f"Command '{base_cmd}' is not in the whitelist")
                
        if policy.command_blacklist is not None and base_cmd in policy.command_blacklist:
            raise PolicyViolationError(f"Command '{base_cmd}' is blacklisted")

        # 3. CWD whitelist/blacklist
        cwd = request.cwd or os.getcwd()
        resolved_cwd = os.path.abspath(cwd)
        
        if policy.allowed_cwds is not None:
            allowed = False
            for acwd in policy.allowed_cwds:
                acwd_res = os.path.abspath(acwd)
                # Check if resolved_cwd is under the allowed path
                if resolved_cwd == acwd_res or resolved_cwd.startswith(acwd_res + os.sep):
                    allowed = True
                    break
            if not allowed:
                raise PolicyViolationError(f"CWD '{cwd}' is not within any allowed paths")

        if policy.blocked_cwds is not None:
            for bcwd in policy.blocked_cwds:
                bcwd_res = os.path.abspath(bcwd)
                if resolved_cwd == bcwd_res or resolved_cwd.startswith(bcwd_res + os.sep):
                    raise PolicyViolationError(f"CWD '{cwd}' is within a blocked path: {bcwd}")

        # 4. Env whitelist/blacklist
        if request.env:
            if policy.env_whitelist is not None:
                for k in request.env:
                    if k not in policy.env_whitelist:
                        raise PolicyViolationError(f"Environment variable '{k}' is not in the whitelist")
                        
            if policy.env_blacklist is not None:
                for k in request.env:
                    if k in policy.env_blacklist:
                        raise PolicyViolationError(f"Environment variable '{k}' is blacklisted")


class PolicyManager:
    """Facade for policy resolution and validation."""

    def __init__(self) -> None:
        self.resolver = PolicyResolver()
        self.validator = PolicyValidator()

    def resolve_and_validate(
        self,
        request: ExecutionRequest,
        engine_policy: ExecutionPolicy | None,
        global_policy: ExecutionPolicy | None
    ) -> ExecutionPolicy:
        """Resolve policies and validate the request."""
        resolved_policy = self.resolver.resolve(request.policy, engine_policy, global_policy)
        self.validator.validate(request, resolved_policy)
        return resolved_policy
