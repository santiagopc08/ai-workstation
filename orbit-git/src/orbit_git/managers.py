"""Domain managers for ORBIT Git."""

from orbit_core.events import EventBus

from orbit_git.events import (
    BlameCompleted,
    BranchCheckedOut,
    BranchCreated,
    BranchDeleted,
    BranchRenamed,
    CherryPickCompleted,
    CloneCompleted,
    CommitCreated,
    DiffGenerated,
    FetchCompleted,
    HistoryLoaded,
    MergeCompleted,
    PullCompleted,
    PushCompleted,
    RebaseCompleted,
    RemoteAdded,
    RemoteRemoved,
    RemoteRenamed,
)
from orbit_git.exceptions import GitCommandError, GitError
from orbit_git.models import (
    BlameLine,
    Branch,
    Commit,
    Diff,
    DiffStats,
    FetchResult,
    MergeResult,
    PullResult,
    PushResult,
    RebaseResult,
    Remote,
    Repository,
    Status,
)
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


class RemoteManager:
    """Manages git remotes."""

    def __init__(self, runner: GitCommandRunner, event_bus: EventBus | None = None) -> None:
        self._runner = runner
        self._event_bus = event_bus

    def list(self, repo: Repository) -> list[Remote]:
        result = self._runner.run(repo, ["remote", "-v"])
        return GitOutputParser.parse_remotes(result.stdout)

    def add(self, repo: Repository, name: str, url: str) -> None:
        url = GitValidator.validate_url(url)
        self._runner.run(repo, ["remote", "add", name, url])
        if self._event_bus:
            self._event_bus.publish(RemoteAdded(repo_path=repo.path, remote_name=name, url=url))

    def remove(self, repo: Repository, name: str) -> None:
        self._runner.run(repo, ["remote", "remove", name])
        if self._event_bus:
            self._event_bus.publish(RemoteRemoved(repo_path=repo.path, remote_name=name))

    def rename(self, repo: Repository, old_name: str, new_name: str) -> None:
        self._runner.run(repo, ["remote", "rename", old_name, new_name])
        if self._event_bus:
            self._event_bus.publish(RemoteRenamed(repo_path=repo.path, old_name=old_name, new_name=new_name))

    def get_url(self, repo: Repository, name: str) -> str:
        result = self._runner.run(repo, ["remote", "get-url", name])
        return result.stdout.strip()

    def set_url(self, repo: Repository, name: str, url: str) -> None:
        url = GitValidator.validate_url(url)
        self._runner.run(repo, ["remote", "set-url", name, url])

    def fetch(self, repo: Repository, name: str) -> FetchResult:
        try:
            # We don't parse updated refs yet, could parse stderr or just assume success.
            # Usually stderr has fetch output.
            self._runner.run(repo, ["fetch", name])
            if self._event_bus:
                self._event_bus.publish(FetchCompleted(repo_path=repo.path, remote_name=name, success=True))
            return FetchResult(success=True)
        except GitCommandError:
            if self._event_bus:
                self._event_bus.publish(FetchCompleted(repo_path=repo.path, remote_name=name, success=False))
            return FetchResult(success=False)

    def pull(self, repo: Repository, name: str, branch: str) -> PullResult:
        try:
            self._runner.run(repo, ["pull", name, branch])
            if self._event_bus:
                self._event_bus.publish(PullCompleted(repo_path=repo.path, remote_name=name, success=True, conflicts=[]))
            return PullResult(success=True, conflicts=[])
        except GitCommandError:
            diff_result = self._runner.run(repo, ["diff", "--name-only", "--diff-filter=U"])
            conflicts = GitOutputParser.parse_conflict_files(diff_result.stdout)
            if self._event_bus:
                self._event_bus.publish(PullCompleted(repo_path=repo.path, remote_name=name, success=False, conflicts=conflicts))
            return PullResult(success=False, conflicts=conflicts)

    def push(self, repo: Repository, name: str, branch: str) -> PushResult:
        try:
            self._runner.run(repo, ["push", name, branch])
            if self._event_bus:
                self._event_bus.publish(PushCompleted(repo_path=repo.path, remote_name=name, success=True, rejected_refs=[]))
            return PushResult(success=True, rejected_refs=[])
        except GitCommandError:
            # We assume current branch failed for now
            if self._event_bus:
                self._event_bus.publish(
                    PushCompleted(repo_path=repo.path, remote_name=name, success=False, rejected_refs=[branch])
                )
            return PushResult(success=False, rejected_refs=[branch])

    def ls_remote(self, url: str) -> dict[str, str]:
        """Runs git ls-remote without requiring a local repository."""
        url = GitValidator.validate_url(url)
        # To run ls-remote without a repo, we can pass None as repo
        result = self._runner.run(None, ["ls-remote", url])
        return GitOutputParser.parse_ls_remote(result.stdout)

    def clone(self, url: str, target_path: str) -> Repository:
        """Clones a repository to target_path."""
        url = GitValidator.validate_url(url)
        # Clone doesn't need an existing repo, it creates one.
        try:
            self._runner.run(None, ["clone", url, target_path])
            if self._event_bus:
                self._event_bus.publish(CloneCompleted(source_url=url, success=True))
        except GitCommandError as e:
            if self._event_bus:
                self._event_bus.publish(CloneCompleted(source_url=url, success=True))
            raise e
            
        return GitValidator.validate_repository(target_path)


class DiffManager:
    """Manages git diffs."""

    def __init__(self, runner: GitCommandRunner, event_bus: EventBus | None = None) -> None:
        self._runner = runner
        self._event_bus = event_bus

    def _get_diff(self, repo: Repository, args: list[str], target: str) -> Diff:
        numstat = self._runner.run(repo, ["diff", "--numstat"] + args)
        name_status = self._runner.run(repo, ["diff", "--name-status"] + args)
        
        stats = GitOutputParser.parse_diff_numstat(numstat.stdout)
        files = GitOutputParser.parse_diff_files(name_status.stdout, numstat.stdout)
        
        diff = Diff(files=files, stats=stats)
        if self._event_bus:
            self._event_bus.publish(DiffGenerated(repo_path=repo.path, target=target))
        return diff

    def diff_working_tree(self, repo: Repository) -> Diff:
        return self._get_diff(repo, [], "working_tree")

    def diff_staged(self, repo: Repository) -> Diff:
        return self._get_diff(repo, ["--staged"], "staged")

    def diff_between(self, repo: Repository, ref_a: str, ref_b: str) -> Diff:
        return self._get_diff(repo, [f"{ref_a}..{ref_b}"], f"{ref_a}..{ref_b}")

    def diff_file(self, repo: Repository, path: str) -> Diff:
        return self._get_diff(repo, ["--", path], path)

    def diff_stat(self, repo: Repository) -> DiffStats:
        result = self._runner.run(repo, ["diff", "--numstat"])
        return GitOutputParser.parse_diff_numstat(result.stdout)


class HistoryManager:
    """Manages git history."""

    def __init__(self, runner: GitCommandRunner, event_bus: EventBus | None = None) -> None:
        self._runner = runner
        self._event_bus = event_bus

    def log(self, repo: Repository) -> list[Commit]:
        result = self._runner.run(repo, ["log", '--format=%H|%an|%s|%aI'])
        commits = GitOutputParser.parse_commits(result.stdout)
        if self._event_bus:
            self._event_bus.publish(HistoryLoaded(repo_path=repo.path, target="all"))
        return commits

    def log_file(self, repo: Repository, path: str) -> list[Commit]:
        result = self._runner.run(repo, ["log", '--format=%H|%an|%s|%aI', "--", path])
        commits = GitOutputParser.parse_commits(result.stdout)
        if self._event_bus:
            self._event_bus.publish(HistoryLoaded(repo_path=repo.path, target=path))
        return commits

    def show(self, repo: Repository, commit_hash: str) -> tuple[Commit, Diff]:
        # get commit details
        result = self._runner.run(repo, ["show", "--no-patch", '--format=%H|%an|%s|%aI', commit_hash])
        commits = GitOutputParser.parse_commits(result.stdout)
        if not commits:
            raise GitError(f"Commit not found: {commit_hash}")
            
        # get diff (for the commit)
        # diff-tree gets the diff of the commit against its parents
        numstat = self._runner.run(repo, ["diff-tree", "--no-commit-id", "--numstat", "-r", commit_hash])
        name_status = self._runner.run(repo, ["diff-tree", "--no-commit-id", "--name-status", "-r", commit_hash])
        
        stats = GitOutputParser.parse_diff_numstat(numstat.stdout)
        files = GitOutputParser.parse_diff_files(name_status.stdout, numstat.stdout)
        
        return commits[0], Diff(files=files, stats=stats)

    def show_file(self, repo: Repository, commit_hash: str, path: str) -> tuple[Commit, Diff]:
        result = self._runner.run(repo, ["show", "--no-patch", '--format=%H|%an|%s|%aI', commit_hash])
        commits = GitOutputParser.parse_commits(result.stdout)
        if not commits:
            raise GitError(f"Commit not found: {commit_hash}")
            
        numstat = self._runner.run(repo, ["diff-tree", "--no-commit-id", "--numstat", "-r", commit_hash, "--", path])
        name_status = self._runner.run(repo, ["diff-tree", "--no-commit-id", "--name-status", "-r", commit_hash, "--", path])
        
        stats = GitOutputParser.parse_diff_numstat(numstat.stdout)
        files = GitOutputParser.parse_diff_files(name_status.stdout, numstat.stdout)
        
        return commits[0], Diff(files=files, stats=stats)

    def blame(self, repo: Repository, path: str) -> list[BlameLine]:
        result = self._runner.run(repo, ["blame", "--line-porcelain", path])
        lines = GitOutputParser.parse_blame_porcelain(result.stdout)
        if self._event_bus:
            self._event_bus.publish(BlameCompleted(repo_path=repo.path, file_path=path))
        return lines

    def parents(self, repo: Repository, commit_hash: str) -> list[str]:
        result = self._runner.run(repo, ["log", "-1", "--format=%P", commit_hash])
        parents_str = result.stdout.strip()
        return parents_str.split() if parents_str else []

    def children(self, repo: Repository, commit_hash: str) -> list[str]:
        # ancestry-path requires a range
        result = self._runner.run(repo, ["rev-list", "--children", "--all"])
        children_map: dict[str, list[str]] = {}
        for line in result.stdout.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                parent = parts[0]
                children_list = parts[1:]
                for _ in children_list:
                    # In `rev-list --children`, the output format is:
                    # <commit> <child1> <child2> ...
                    # Actually, `git rev-list --children --all` prints `<commit> <child>...`
                    # where <child> are commits that have <commit> as a parent.
                    if parent not in children_map:
                        children_map[parent] = []
                    children_map[parent].extend(children_list)
                    break # The line format is: commit [child1 child2...]
                    
        return children_map.get(commit_hash, [])
