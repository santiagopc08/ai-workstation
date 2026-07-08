"""Domain managers for ORBIT Git."""

from orbit_git.models import Repository, Status
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
