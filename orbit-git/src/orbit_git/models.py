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


@dataclass(frozen=True, slots=True)
class Remote:
    """A Git remote."""
    name: str
    url: str
    push_url: str


@dataclass(frozen=True, slots=True)
class FetchResult:
    """Result of a fetch operation."""
    success: bool
    updated_refs: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PullResult:
    """Result of a pull operation."""
    success: bool
    conflicts: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class PushResult:
    """Result of a push operation."""
    success: bool
    rejected_refs: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class DiffStats:
    """Statistics for a diff."""
    files_changed: int
    insertions: int
    deletions: int


@dataclass(frozen=True, slots=True)
class DiffFile:
    """A file in a diff."""
    path: str
    status: str
    old_path: str | None = None
    insertions: int = 0
    deletions: int = 0
    patch: str | None = None


@dataclass(frozen=True, slots=True)
class Diff:
    """A collection of diff files and stats."""
    files: list[DiffFile] = field(default_factory=list)
    stats: DiffStats = field(default_factory=lambda: DiffStats(0, 0, 0))


@dataclass(frozen=True, slots=True)
class BlameLine:
    """A line from git blame."""
    line_number: int
    commit_hash: str
    author: str
    date: str
    content: str


@dataclass(frozen=True, slots=True)
class CommitReference:
    """Reference to a commit (just the hash)."""
    hash: str
