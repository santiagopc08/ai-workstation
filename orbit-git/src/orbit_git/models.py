"""Data models for ORBIT Git."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class RepositoryState(Enum):
    """The current state of a Git repository."""
    CLEAN = "CLEAN"
    MERGING = "MERGING"
    REBASING = "REBASING"
    CHERRY_PICKING = "CHERRY_PICKING"
    REVERTING = "REVERTING"
    BISECTING = "BISECTING"
    DETACHED_HEAD = "DETACHED_HEAD"


@dataclass(frozen=True, slots=True)
class Repository:
    """Handle to an opened, validated Git repository."""
    path: str
    real_path: str
    is_bare: bool
    state: RepositoryState


@dataclass(frozen=True, slots=True)
class GitVersion:
    """Parsed Git binary version."""
    version_str: str
    major: int
    minor: int
    patch: int


@dataclass(frozen=True, slots=True)
class GitResult:
    """Internal result from GitCommandRunner."""
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int


@dataclass(frozen=True, slots=True)
class StatusEntry:
    """A file entry in git status."""
    path: str
    status: str
    old_path: str | None = None


@dataclass(frozen=True, slots=True)
class Status:
    """The working tree status."""
    staged: list[StatusEntry] = field(default_factory=list)
    unstaged: list[StatusEntry] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)
    branch: str = ""
    upstream: str | None = None
    ahead: int = 0
    behind: int = 0

@dataclass(frozen=True, slots=True)
class Branch:
    """A Git branch."""
    name: str
    commit_hash: str
    is_current: bool
    upstream: str | None = None


@dataclass(frozen=True, slots=True)
class Commit:
    """A Git commit."""
    hash: str
    author: str
    message: str
    date: str


@dataclass(frozen=True, slots=True)
class MergeResult:
    """Result of a merge operation."""
    success: bool
    conflicts: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class RebaseResult:
    """Result of a rebase operation."""
    success: bool
    conflicts: list[str] = field(default_factory=list)
