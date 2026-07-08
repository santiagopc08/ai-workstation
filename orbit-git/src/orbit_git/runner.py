"""Command runner for ORBIT Git."""

from orbit_git.exceptions import GitCommandError
from orbit_git.models import GitResult, Repository
from orbit_git.providers import GitProvider


class GitCommandRunner:
    """Translates domain calls into GitProvider calls."""

    def __init__(self, provider: GitProvider) -> None:
        self._provider = provider

    def run(self, repo: Repository | None, args: list[str]) -> GitResult:
        """Run a git command in the context of a repository."""
        
        # Base environment setup
        env = {
            "GIT_TERMINAL_PROMPT": "0",  # Disable interactive prompts
            "GIT_ASKPASS": "echo",       # Disable password prompts
        }
        
        repo_path = repo.path if repo else None
        
        result = self._provider.run(repo_path, args, env=env)
        
        if not result.success:
            raise GitCommandError(
                message=f"Git command failed: git {' '.join(args)}",
                exit_code=result.exit_code,
                stderr=result.stderr.strip()
            )
            
        return result
