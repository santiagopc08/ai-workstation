"""Output parser for ORBIT Git."""

import re
from pathlib import Path

from orbit_git.exceptions import GitError
from orbit_git.models import Branch, Commit, GitVersion, RepositoryState, Status, StatusEntry


class GitOutputParser:
    """Parses raw git output into structured models."""

    VERSION_PATTERN = re.compile(r"git version (\d+)\.(\d+)\.(\d+)")

    @staticmethod
    def parse_version(output: str) -> GitVersion:
        """Parse `git --version` output."""
        match = GitOutputParser.VERSION_PATTERN.search(output)
        if not match:
            raise GitError(f"Could not parse git version from: {output}")
        
        return GitVersion(
            version_str=match.group(0),
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3))
        )

    @staticmethod
    def parse_status(output: str) -> Status:
        """Parse `git status --porcelain=v2 --branch` output."""
        status = Status()
        
        for line in output.splitlines():
            if not line:
                continue
                
            if line.startswith("# branch.oid "):
                # Can be initial (hash or '(initial)')
                pass
            elif line.startswith("# branch.head "):
                status = Status(
                    staged=status.staged,
                    unstaged=status.unstaged,
                    untracked=status.untracked,
                    branch=line[14:],
                    upstream=status.upstream,
                    ahead=status.ahead,
                    behind=status.behind
                )
            elif line.startswith("# branch.upstream "):
                status = Status(
                    staged=status.staged,
                    unstaged=status.unstaged,
                    untracked=status.untracked,
                    branch=status.branch,
                    upstream=line[18:],
                    ahead=status.ahead,
                    behind=status.behind
                )
            elif line.startswith("# branch.ab "):
                # Format: # branch.ab +1 -2
                parts = line.split(" ")
                ahead = int(parts[2][1:])
                behind = int(parts[3][1:])
                status = Status(
                    staged=status.staged,
                    unstaged=status.unstaged,
                    untracked=status.untracked,
                    branch=status.branch,
                    upstream=status.upstream,
                    ahead=ahead,
                    behind=behind
                )
            elif line.startswith("1 ") or line.startswith("2 "):
                # Format 1: 1 <XY> <sub> <mH> <mI> <mW> <hH> <hI> <path>
                # Format 2 (rename): 2 <XY> <sub> <mH> <mI> <mW> <hH> <hI> <X><score> <path><sep><origPath>
                parts = line.split(" ")
                xy = parts[1]
                x, y = xy[0], xy[1]
                
                path_part = parts[-1]
                old_path = None
                
                if line.startswith("2 "):
                    # Renames have path\torigPath
                    paths = path_part.split("\t")
                    if len(paths) == 2:
                        path_part = paths[0]
                        old_path = paths[1]
                
                staged_list = list(status.staged)
                unstaged_list = list(status.unstaged)
                
                if x != ".":
                    staged_list.append(StatusEntry(path=path_part, status=x, old_path=old_path))
                if y != ".":
                    unstaged_list.append(StatusEntry(path=path_part, status=y))
                    
                status = Status(
                    staged=staged_list,
                    unstaged=unstaged_list,
                    untracked=status.untracked,
                    branch=status.branch,
                    upstream=status.upstream,
                    ahead=status.ahead,
                    behind=status.behind
                )
            elif line.startswith("? "):
                untracked_list = list(status.untracked)
                untracked_list.append(line[2:])
                status = Status(
                    staged=status.staged,
                    unstaged=status.unstaged,
                    untracked=untracked_list,
                    branch=status.branch,
                    upstream=status.upstream,
                    ahead=status.ahead,
                    behind=status.behind
                )
        
        return status

    @staticmethod
    def get_repository_state(git_dir: Path) -> RepositoryState:
        """Infer the repository state by checking for specific files in .git/."""
        if (git_dir / "rebase-merge").exists() or (git_dir / "rebase-apply").exists():
            return RepositoryState.REBASING
        elif (git_dir / "MERGE_HEAD").exists():
            return RepositoryState.MERGING
        elif (git_dir / "CHERRY_PICK_HEAD").exists():
            return RepositoryState.CHERRY_PICKING
        elif (git_dir / "REVERT_HEAD").exists():
            return RepositoryState.REVERTING
        elif (git_dir / "BISECT_LOG").exists():
            return RepositoryState.BISECTING
            
        # Check detached HEAD
        head_file = git_dir / "HEAD"
        if head_file.exists():
            head_content = head_file.read_text().strip()
            if not head_content.startswith("ref:"):
                return RepositoryState.DETACHED_HEAD
                
        return RepositoryState.CLEAN

    @staticmethod
    def parse_branches(output: str) -> list[Branch]:
        """Parse `git branch --format="%(refname:short)|%(objectname)|%(HEAD)|%(upstream:short)"`"""
        branches = []
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("|")
            if len(parts) >= 3:
                name = parts[0]
                commit_hash = parts[1]
                is_current = parts[2] == "*"
                upstream = parts[3] if len(parts) > 3 and parts[3] else None
                branches.append(Branch(name=name, commit_hash=commit_hash, is_current=is_current, upstream=upstream))
        return branches

    @staticmethod
    def parse_commits(output: str) -> list[Commit]:
        """Parse `git log --format="%H|%an|%s|%aI"`"""
        commits = []
        for line in output.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split("|", maxsplit=3)
            if len(parts) == 4:
                commits.append(Commit(hash=parts[0], author=parts[1], message=parts[2], date=parts[3]))
        return commits

    @staticmethod
    def parse_conflict_files(output: str) -> list[str]:
        """Parse `git diff --name-only --diff-filter=U`"""
        return [line.strip() for line in output.splitlines() if line.strip()]
