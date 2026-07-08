"""Domain managers for ORBIT Git."""

from orbit_core.events import EventBus

from orbit_git.events import (
    BranchCheckedOut,
    BranchCreated,
    BranchDeleted,
    BranchRenamed,
    CherryPickCompleted,
    CommitCreated,
    MergeCompleted,
    RebaseCompleted,
)
from orbit_git.exceptions import GitCommandError
from orbit_git.models import Branch, Commit, MergeResult, RebaseResult, Repository, Status
from orbit_git.parser import GitOutputParser
from orbit_git.runner import GitCommandRunner
from orbit_git.validator import GitValidator


class RepositoryManager:
    """Manages repository discovery and status."""

    def __init__(self, runner: GitCommandRunner) -> None:
        self._runner = runner

    def discover(self, start_path: str) -> str:
        """Climb up the directory tree to find a Git repository."""
        return GitValidator.discover_repository(start_path)

    def open(self, path: str) -> Repository:
        """Validate and open a Git repository."""
        # Validation checks the .git dir and constructs the Repository model
        return GitValidator.validate_repository(path)

    def close(self, repo: Repository) -> None:
        """Release a repository handle. (No-op in sprint 1)"""
        # In the future, this might release locks or file handles.
        pass

    def status(self, repo: Repository) -> Status:
        """Get the working tree status."""
        result = self._runner.run(repo, ["status", "--porcelain=v2", "--branch"])
        return GitOutputParser.parse_status(result.stdout)


class BranchManager:
    """Manages git branches."""

    def __init__(self, runner: GitCommandRunner, event_bus: EventBus | None = None) -> None:
        self._runner = runner
        self._event_bus = event_bus

    def list(self, repo: Repository) -> list[Branch]:
        result = self._runner.run(repo, ["branch", "--format=%(refname:short)|%(objectname)|%(HEAD)|%(upstream:short)"])
        return GitOutputParser.parse_branches(result.stdout)

    def current(self, repo: Repository) -> Branch:
        branches = self.list(repo)
        for b in branches:
            if b.is_current:
                return b
        raise GitCommandError("No current branch found (possibly detached HEAD).", exit_code=1, stderr="")

    def create(self, repo: Repository, name: str) -> None:
        self._runner.run(repo, ["branch", name])
        if self._event_bus:
            self._event_bus.publish(BranchCreated(repo_path=repo.path, branch_name=name))

    def delete(self, repo: Repository, name: str) -> None:
        self._runner.run(repo, ["branch", "-d", name])
        if self._event_bus:
            self._event_bus.publish(BranchDeleted(repo_path=repo.path, branch_name=name))

    def rename(self, repo: Repository, old_name: str, new_name: str) -> None:
        self._runner.run(repo, ["branch", "-m", old_name, new_name])
        if self._event_bus:
            self._event_bus.publish(BranchRenamed(repo_path=repo.path, old_name=old_name, new_name=new_name))

    def checkout(self, repo: Repository, name: str) -> None:
        self._runner.run(repo, ["checkout", name])
        if self._event_bus:
            self._event_bus.publish(BranchCheckedOut(repo_path=repo.path, branch_name=name))

    def merge(self, repo: Repository, name: str) -> MergeResult:
        try:
            self._runner.run(repo, ["merge", name])
            if self._event_bus:
                self._event_bus.publish(MergeCompleted(repo_path=repo.path, branch_name=name, success=True, conflicts=[]))
            return MergeResult(success=True, conflicts=[])
        except GitCommandError:
            # Parse conflicts
            diff_result = self._runner.run(repo, ["diff", "--name-only", "--diff-filter=U"])
            conflicts = GitOutputParser.parse_conflict_files(diff_result.stdout)
            if self._event_bus:
                self._event_bus.publish(MergeCompleted(repo_path=repo.path, branch_name=name, success=False, conflicts=conflicts))
            return MergeResult(success=False, conflicts=conflicts)

    def rebase(self, repo: Repository, name: str) -> RebaseResult:
        try:
            self._runner.run(repo, ["rebase", name])
            if self._event_bus:
                self._event_bus.publish(RebaseCompleted(repo_path=repo.path, branch_name=name, success=True, conflicts=[]))
            return RebaseResult(success=True, conflicts=[])
        except GitCommandError:
            diff_result = self._runner.run(repo, ["diff", "--name-only", "--diff-filter=U"])
            conflicts = GitOutputParser.parse_conflict_files(diff_result.stdout)
            if self._event_bus:
                self._event_bus.publish(
                    RebaseCompleted(repo_path=repo.path, branch_name=name, success=False, conflicts=conflicts)
                )
            return RebaseResult(success=False, conflicts=conflicts)


class CommitManager:
    """Manages git commits."""

    def __init__(self, runner: GitCommandRunner, event_bus: EventBus | None = None) -> None:
        self._runner = runner
        self._event_bus = event_bus

    def add(self, repo: Repository, paths: list[str]) -> None:
        self._runner.run(repo, ["add", "--"] + paths)

    def add_all(self, repo: Repository) -> None:
        self._runner.run(repo, ["add", "--all"])

    def create(self, repo: Repository, message: str) -> Commit:
        self._runner.run(repo, ["commit", "-m", message])
        # Retrieve the newly created commit
        result = self._runner.run(repo, ["log", "-1", "--format=%H|%an|%s|%aI"])
        commits = GitOutputParser.parse_commits(result.stdout)
        commit = commits[0]
        if self._event_bus:
            self._event_bus.publish(CommitCreated(repo_path=repo.path, commit_hash=commit.hash, message=commit.message))
        return commit

    def amend(self, repo: Repository, message: str | None = None) -> Commit:
        args = ["commit", "--amend"]
        if message:
            args.extend(["-m", message])
        else:
            args.append("--no-edit")
        self._runner.run(repo, args)
        
        result = self._runner.run(repo, ["log", "-1", "--format=%H|%an|%s|%aI"])
        commits = GitOutputParser.parse_commits(result.stdout)
        commit = commits[0]
        if self._event_bus:
            self._event_bus.publish(CommitCreated(repo_path=repo.path, commit_hash=commit.hash, message=commit.message))
        return commit

    def show(self, repo: Repository, hash_val: str) -> Commit:
        result = self._runner.run(repo, ["show", "-s", "--format=%H|%an|%s|%aI", hash_val])
        commits = GitOutputParser.parse_commits(result.stdout)
        if not commits:
            raise GitCommandError(f"Commit {hash_val} not found", exit_code=1, stderr="")
        return commits[0]

    def cherry_pick(self, repo: Repository, hash_val: str) -> MergeResult:
        try:
            self._runner.run(repo, ["cherry-pick", hash_val])
            if self._event_bus:
                self._event_bus.publish(
                    CherryPickCompleted(repo_path=repo.path, commit_hash=hash_val, success=True, conflicts=[])
                )
            return MergeResult(success=True, conflicts=[])
        except GitCommandError:
            diff_result = self._runner.run(repo, ["diff", "--name-only", "--diff-filter=U"])
            conflicts = GitOutputParser.parse_conflict_files(diff_result.stdout)
            if self._event_bus:
                self._event_bus.publish(
                    CherryPickCompleted(repo_path=repo.path, commit_hash=hash_val, success=False, conflicts=conflicts)
                )
            return MergeResult(success=False, conflicts=conflicts)
