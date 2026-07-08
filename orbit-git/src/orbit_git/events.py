"""Events for ORBIT Git."""

from dataclasses import dataclass

from orbit_core.events import Event


@dataclass(frozen=True, slots=True)
class GitEvent(Event):
    """Base for all ORBIT Git events."""
    repo_path: str = ""


@dataclass(frozen=True, slots=True)
class BranchCreated(GitEvent):
    branch_name: str = ""


@dataclass(frozen=True, slots=True)
class BranchDeleted(GitEvent):
    branch_name: str = ""


@dataclass(frozen=True, slots=True)
class BranchRenamed(GitEvent):
    old_name: str = ""
    new_name: str = ""


@dataclass(frozen=True, slots=True)
class BranchCheckedOut(GitEvent):
    branch_name: str = ""


@dataclass(frozen=True, slots=True)
class MergeCompleted(GitEvent):
    branch_name: str = ""
    success: bool = True
    conflicts: list[str] | None = None


@dataclass(frozen=True, slots=True)
class RebaseCompleted(GitEvent):
    branch_name: str = ""
    success: bool = True
    conflicts: list[str] | None = None


@dataclass(frozen=True, slots=True)
class CommitCreated(GitEvent):
    commit_hash: str = ""
    message: str = ""


@dataclass(frozen=True, slots=True)
class CherryPickCompleted(GitEvent):
    commit_hash: str = ""
    success: bool = True
    conflicts: list[str] | None = None
