"""Tests for ORBIT Git Sprint 1."""

import os
import subprocess
from pathlib import Path

import pytest
from orbit_execution import ExecutionEngine

from orbit_git import GitEngine, RepositoryNotFoundError, RepositoryState


@pytest.fixture
def execution_engine() -> ExecutionEngine:
    return ExecutionEngine()


@pytest.fixture
def git_engine(execution_engine: ExecutionEngine) -> GitEngine:
    return GitEngine(execution_engine)


def test_git_version(git_engine: GitEngine) -> None:
    version = git_engine.version()
    assert version.startswith("git version ")
    assert len(version.split(".")) >= 2


def test_discover_and_open_repo(git_engine: GitEngine, tmp_path: Path) -> None:
    # Init a repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    
    # Create a nested dir
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    
    # Discover
    discovered_path = git_engine.discover(str(nested))
    assert os.path.realpath(discovered_path) == os.path.realpath(str(tmp_path))
    
    # Open
    repo = git_engine.open(discovered_path)
    assert repo.is_bare is False
    assert repo.state == RepositoryState.CLEAN


def test_open_bare_repo(git_engine: GitEngine, tmp_path: Path) -> None:
    subprocess.run(["git", "init", "--bare"], cwd=tmp_path, check=True)
    
    repo = git_engine.open(str(tmp_path))
    assert repo.is_bare is True
    assert repo.state == RepositoryState.CLEAN


def test_open_invalid_repo(git_engine: GitEngine, tmp_path: Path) -> None:
    with pytest.raises(RepositoryNotFoundError):
        git_engine.open(str(tmp_path))


def test_status_clean_modified_untracked(git_engine: GitEngine, tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    
    repo = git_engine.open(str(tmp_path))
    
    # Empty status
    status = git_engine.status(repo)
    assert not status.staged
    assert not status.unstaged
    assert not status.untracked
    
    # Create file
    f1 = tmp_path / "file1.txt"
    f1.write_text("hello")
    
    status = git_engine.status(repo)
    assert status.untracked == ["file1.txt"]
    
    # Add file
    subprocess.run(["git", "add", "file1.txt"], cwd=tmp_path, check=True)
    
    status = git_engine.status(repo)
    assert len(status.staged) == 1
    assert status.staged[0].path == "file1.txt"
    assert status.staged[0].status == "A"
    
    # Commit
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True)
    
    # Modify
    f1.write_text("world")
    
    status = git_engine.status(repo)
    assert len(status.unstaged) == 1
    assert status.unstaged[0].path == "file1.txt"
    assert status.unstaged[0].status == "M"
    assert status.branch in ("master", "main")
    
    # Detached head test
    subprocess.run(["git", "checkout", "--detach"], cwd=tmp_path, check=True)
    repo2 = git_engine.open(str(tmp_path))
    assert repo2.state == RepositoryState.DETACHED_HEAD
