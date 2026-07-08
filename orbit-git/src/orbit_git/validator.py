"""Pre-flight validations for ORBIT Git."""

import os
from pathlib import Path
from urllib.parse import urlparse

from orbit_git.exceptions import GitError, RepositoryCorruptError, RepositoryNotFoundError
from orbit_git.models import Repository, RepositoryState
from orbit_git.parser import GitOutputParser


class GitValidator:
    """Performs pre-flight checks and resolves repository contexts."""

    @staticmethod
    def validate_repository(path: str) -> Repository:
        """
        Validate that the path is a Git repository, resolve symlinks,
        check bare vs non-bare, and determine state.
        """
        if not os.path.exists(path):
            raise RepositoryNotFoundError(f"Path does not exist: {path}")

        real_path = os.path.realpath(path)
        p = Path(real_path)

        # Standard non-bare repo
        if (p / ".git").is_dir() or (p / ".git").is_file():  # .git can be a file for worktrees
            git_dir = p / ".git"
            # It's a non-bare repository
            if not GitValidator._is_valid_git_dir(git_dir):
                raise RepositoryCorruptError(f"Repository at {real_path} appears corrupt.")
            
            state = GitOutputParser.get_repository_state(git_dir)
            return Repository(
                path=path,
                real_path=real_path,
                is_bare=False,
                state=state
            )

        # Bare repo
        if GitValidator._is_valid_git_dir(p):
            return Repository(
                path=path,
                real_path=real_path,
                is_bare=True,
                state=RepositoryState.CLEAN  # Bare repos don't have worktrees to be in REBASING state
            )

        raise RepositoryNotFoundError(f"Not a git repository: {real_path}")

    @staticmethod
    def _is_valid_git_dir(git_dir: Path) -> bool:
        """Check if a directory contains essential Git metadata."""
        if git_dir.is_file():
            # Usually worktrees have a `.git` file that points to the actual gitdir
            # For sprint 1, we will just assume it's valid if it exists.
            return True
            
        has_objects = (git_dir / "objects").is_dir()
        has_refs = (git_dir / "refs").is_dir()
        has_head = (git_dir / "HEAD").is_file()
        
        return has_objects and has_refs and has_head

    @staticmethod
    def discover_repository(start_path: str) -> str:
        """Climb up the directory tree to find a Git repository."""
        current = Path(os.path.realpath(start_path))
        
        while True:
            if (current / ".git").exists() or GitValidator._is_valid_git_dir(current):
                return str(current)
            
            parent = current.parent
            if parent == current:
                break
            current = parent
            
        raise RepositoryNotFoundError(f"Could not find a git repository starting from {start_path}")

    @staticmethod
    def validate_url(url: str) -> str:
        """
        Validate remote URL to prevent security issues like embedded credentials
        or disallowed protocols.
        """
        if not url:
            raise GitError("URL cannot be empty")
            
        if url.startswith("ext::"):
            raise GitError("Remote-ext protocol (ext::) is forbidden for security reasons.")
            
        # Try to parse to check for credentials if it's a standard URL (http/https/ssh/git)
        # However, SSH paths like user@host:repo.git might not parse perfectly via urlparse without scheme.
        
        # Check for explicit user:pass@ in the URL
        if "://" in url:
            parsed = urlparse(url)
            if parsed.scheme not in ["http", "https", "ssh", "git", "file"]:
                raise GitError(f"Unsupported protocol: {parsed.scheme}")
            if parsed.password:
                raise GitError("Embedded credentials in URLs are forbidden.")
                
        # For SSH scp-like syntax (user@host:path), we just block passwords
        # E.g., user:pass@host:path is blocked by simple substring check
        # But user@host is fine.
        if "@" in url:
            auth_part = url.split("@", 1)[0]
            if ":" in auth_part and "://" not in auth_part:
                # E.g., user:pass@host...
                # Note: this might incorrectly flag ipv6, but typically git urls don't use raw ipv6 without brackets
                raise GitError("Embedded credentials in URLs are forbidden.")
                
        return url
