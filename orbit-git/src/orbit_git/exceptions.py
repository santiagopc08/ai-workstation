"""Exceptions for ORBIT Git."""

from orbit_core.exceptions import OrbitError


class GitError(OrbitError):
    """Base for all ORBIT Git failures."""


class RepositoryNotFoundError(GitError):
    """Path is not a Git repository."""


class RepositoryCorruptError(GitError):
    """Repository is missing essential Git internals."""


class GitCommandError(GitError):
    """A Git command exited with non-zero."""
    
    def __init__(self, message: str, exit_code: int, stderr: str) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.stderr = stderr
