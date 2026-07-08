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


@dataclass(frozen=True, slots=True)
class RemoteAdded(GitEvent):
    remote_name: str = ""
    url: str = ""


@dataclass(frozen=True, slots=True)
class RemoteRemoved(GitEvent):
    remote_name: str = ""


@dataclass(frozen=True, slots=True)
class RemoteRenamed(GitEvent):
    old_name: str = ""
    new_name: str = ""


@dataclass(frozen=True, slots=True)
class FetchCompleted(GitEvent):
    remote_name: str = ""
    success: bool = True


@dataclass(frozen=True, slots=True)
class PullCompleted(GitEvent):
    remote_name: str = ""
    success: bool = True
    conflicts: list[str] | None = None


@dataclass(frozen=True, slots=True)
class PushCompleted(GitEvent):
    remote_name: str = ""
    success: bool = True
    rejected_refs: list[str] | None = None


@dataclass(frozen=True, slots=True)
class CloneCompleted(GitEvent):
    source_url: str = ""
    success: bool = True


@dataclass(frozen=True, slots=True)
class DiffGenerated(GitEvent):
    target: str = ""  # e.g. "working_tree", "staged", "commit", "file_path"


@dataclass(frozen=True, slots=True)
class HistoryLoaded(GitEvent):
    target: str = ""


@dataclass(frozen=True, slots=True)
class BlameCompleted(GitEvent):
    file_path: str = ""
