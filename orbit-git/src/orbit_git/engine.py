"""ORBIT Git Engine Facade."""

from orbit_core.events import EventBus
from orbit_execution import ExecutionEngine

from orbit_git.managers import BranchManager, CommitManager, RepositoryManager
from orbit_git.models import Repository, Status
from orbit_git.parser import GitOutputParser
from orbit_git.providers import LocalGitProvider
from orbit_git.runner import GitCommandRunner


class GitEngine:
    """The main entry point for all Git operations in the ORBIT platform."""

    def __init__(self, execution_engine: ExecutionEngine, event_bus: EventBus | None = None) -> None:
        self._provider = LocalGitProvider(execution_engine)
        self._runner = GitCommandRunner(self._provider)
        
        self._repo_manager = RepositoryManager(self._runner)
        self._branch_manager = BranchManager(self._runner, event_bus)
        self._commit_manager = CommitManager(self._runner, event_bus)

    def version(self) -> str:
        """Get the parsed git version."""
        raw_version = self._provider.version()
        parsed = GitOutputParser.parse_version(raw_version)
        return parsed.version_str

    def discover(self, start_path: str) -> str:
        """Climb up the directory tree to find a Git repository."""
        return self._repo_manager.discover(start_path)

    def open(self, path: str) -> Repository:
        """Validate and open a Git repository."""
        return self._repo_manager.open(path)

    def close(self, repo: Repository) -> None:
        """Release a repository handle."""
        self._repo_manager.close(repo)

    def status(self, repo: Repository) -> Status:
        """Get the working tree status."""
        return self._repo_manager.status(repo)

    def branches(self) -> BranchManager:
        """Get the branch manager."""
        return self._branch_manager

    def commits(self) -> CommitManager:
        """Get the commit manager."""
        return self._commit_manager
