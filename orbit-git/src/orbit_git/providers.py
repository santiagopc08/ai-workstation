"""Execution providers for ORBIT Git."""

import shutil
from typing import Protocol

from orbit_execution import ExecutionEngine, ExecutionRequest

from orbit_git.exceptions import GitError
from orbit_git.models import GitResult


class GitProvider(Protocol):
    """SPI for Git execution backends."""
    
    def run(self, repo_path: str | None, args: list[str], env: dict[str, str] | None = None) -> GitResult:
        """Run a git command and return the result."""
        ...
        
    def version(self) -> str:
        """Get the raw git version string."""
        ...


class LocalGitProvider(GitProvider):
    """Executes git via the local binary through ExecutionEngine."""

    def __init__(self, execution_engine: ExecutionEngine) -> None:
        self._engine = execution_engine
        
        # Verify git is available
        self._git_path = shutil.which("git")
        if not self._git_path:
            raise GitError("Git executable not found in PATH")

    def run(self, repo_path: str | None, args: list[str], env: dict[str, str] | None = None) -> GitResult:
        """Run a git command through ExecutionEngine."""
        command = [self._git_path] + args
        
        request = ExecutionRequest(
            command=command,
            cwd=repo_path,
            env=env or {}
        )
        
        # execution_engine raises ExecutionError on timeout or policy violation,
        # but returns a CompletedProcess on process exit (even if non-zero exit_code).
        result = self._engine.execute(request)
        
        return GitResult(
            success=result.success,
            stdout=result.process.stdout.decode("utf-8", errors="replace"),
            stderr=result.process.stderr.decode("utf-8", errors="replace"),
            exit_code=result.process.exit_code,
            duration_ms=result.process.duration_ms
        )

    def version(self) -> str:
        """Run `git --version`."""
        result = self.run(None, ["--version"])
        if not result.success:
            raise GitError(f"Failed to get git version: {result.stderr}")
        return result.stdout.strip()
