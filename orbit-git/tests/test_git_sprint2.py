"""Tests for ORBIT Git Sprint 2 (Branches & Commits)."""

import subprocess
from pathlib import Path

import pytest
from orbit_core.events import EventBus
from orbit_execution import ExecutionEngine

from orbit_git import GitEngine, Repository, RepositoryNotFoundError, RepositoryState
from orbit_git.events import BranchCreated, CommitCreated, GitEvent, MergeCompleted


@pytest.fixture
def execution_engine() -> ExecutionEngine:
    return ExecutionEngine()


@pytest.fixture
def event_bus() -> EventBus:
    return EventBus()


@pytest.fixture
def git_engine(execution_engine: ExecutionEngine, event_bus: EventBus) -> GitEngine:
    return GitEngine(execution_engine, event_bus)


@pytest.fixture
def repo(git_engine: GitEngine, tmp_path: Path) -> Repository:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=tmp_path, check=True)
    return git_engine.open(str(tmp_path))


def test_commit_lifecycle(git_engine: GitEngine, repo: Repository, tmp_path: Path, event_bus: EventBus) -> None:
    events: list[GitEvent] = []
    event_bus.subscribe(CommitCreated, lambda e: events.append(e))

    # Add and commit
    f = tmp_path / "file.txt"
    f.write_text("hello")
    
    commits = git_engine.commits()
    commits.add_all(repo)
    commit = commits.create(repo, "initial commit")
    
    assert commit.message == "initial commit"
    assert len(events) == 1
    assert isinstance(events[0], CommitCreated)
    assert events[0].commit_hash == commit.hash
    
    # Amend
    f.write_text("hello world")
    commits.add_all(repo)
    commit2 = commits.amend(repo, "initial commit amended")
    
    assert commit2.message == "initial commit amended"
    assert commit2.hash != commit.hash
    assert len(events) == 2
    
    # Show
    fetched_commit = commits.show(repo, commit2.hash)
    assert fetched_commit.hash == commit2.hash


def test_branch_lifecycle(git_engine: GitEngine, repo: Repository, tmp_path: Path, event_bus: EventBus) -> None:
    # Need at least one commit to branch
    f = tmp_path / "file.txt"
    f.write_text("hello")
    commits = git_engine.commits()
    commits.add_all(repo)
    commits.create(repo, "init")
    
    branches = git_engine.branches()
    
    # Create
    branches.create(repo, "feature")
    
    # List
    all_branches = branches.list(repo)
    assert len(all_branches) == 2
    assert any(b.name == "feature" for b in all_branches)
    
    # Checkout
    branches.checkout(repo, "feature")
    current = branches.current(repo)
    assert current.name == "feature"
    assert current.is_current is True
    
    # Rename
    branches.rename(repo, "feature", "feature-new")
    current = branches.current(repo)
    assert current.name == "feature-new"
    
    # Delete (must checkout something else first)
    branches.checkout(repo, "master")
    branches.delete(repo, "feature-new")
    
    all_branches = branches.list(repo)
    assert len(all_branches) == 1


def test_merge_fast_forward(git_engine: GitEngine, repo: Repository, tmp_path: Path) -> None:
    f = tmp_path / "file.txt"
    f.write_text("hello")
    commits = git_engine.commits()
    commits.add_all(repo)
    commits.create(repo, "init")
    
    branches = git_engine.branches()
    branches.create(repo, "feature")
    branches.checkout(repo, "feature")
    
    f.write_text("hello world")
    commits.add_all(repo)
    commits.create(repo, "update")
    
    branches.checkout(repo, "master")
    result = branches.merge(repo, "feature")
    
    assert result.success is True
    assert not result.conflicts


def test_merge_conflict(git_engine: GitEngine, repo: Repository, tmp_path: Path) -> None:
    f = tmp_path / "file.txt"
    f.write_text("hello")
    commits = git_engine.commits()
    commits.add_all(repo)
    commits.create(repo, "init")
    
    branches = git_engine.branches()
    branches.create(repo, "feature")
    
    # Master commit
    f.write_text("hello master")
    commits.add_all(repo)
    commits.create(repo, "master update")
    
    # Feature commit
    branches.checkout(repo, "feature")
    f.write_text("hello feature")
    commits.add_all(repo)
    commits.create(repo, "feature update")
    
    branches.checkout(repo, "master")
    result = branches.merge(repo, "feature")
    
    assert result.success is False
    assert "file.txt" in result.conflicts
