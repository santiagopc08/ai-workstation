"""Tests for ORBIT Git Sprint 3 (Remotes)."""

import subprocess
from pathlib import Path

import pytest
from orbit_core.events import EventBus
from orbit_execution import ExecutionEngine

from orbit_git import GitEngine, GitError, Repository
from orbit_git.events import (
    GitEvent,
    RemoteAdded,
    RemoteRemoved,
    RemoteRenamed,
)


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


@pytest.fixture
def bare_repo(git_engine: GitEngine, tmp_path: Path) -> str:
    bare_path = tmp_path / "bare.git"
    bare_path.mkdir()
    subprocess.run(["git", "init", "--bare"], cwd=bare_path, check=True)
    return str(bare_path)


def test_remote_lifecycle(git_engine: GitEngine, repo: Repository, event_bus: EventBus) -> None:
    events: list[GitEvent] = []
    for evt_type in [RemoteAdded, RemoteRemoved, RemoteRenamed]:
        event_bus.subscribe(evt_type, lambda e: events.append(e))
        
    remotes = git_engine.remotes()
    
    # Add
    remotes.add(repo, "origin", "https://github.com/test/repo.git")
    all_remotes = remotes.list(repo)
    assert len(all_remotes) == 1
    assert all_remotes[0].name == "origin"
    assert all_remotes[0].url == "https://github.com/test/repo.git"
    assert len(events) == 1
    
    # Get URL
    assert remotes.get_url(repo, "origin") == "https://github.com/test/repo.git"
    
    # Rename
    remotes.rename(repo, "origin", "upstream")
    assert remotes.get_url(repo, "upstream") == "https://github.com/test/repo.git"
    assert len(events) == 2
    
    # Set URL
    remotes.set_url(repo, "upstream", "https://github.com/test/repo2.git")
    assert remotes.get_url(repo, "upstream") == "https://github.com/test/repo2.git"
    
    # Remove
    remotes.remove(repo, "upstream")
    assert len(remotes.list(repo)) == 0
    assert len(events) == 3


def test_clone_and_push(git_engine: GitEngine, tmp_path: Path, bare_repo: str) -> None:
    # Clone the bare repo
    clone_path = tmp_path / "clone"
    repo = git_engine.clone(bare_repo, str(clone_path))
    assert repo.path == str(clone_path)
    
    # Commit something
    f = clone_path / "file.txt"
    f.write_text("hello")
    commits = git_engine.commits()
    commits.add_all(repo)
    commits.create(repo, "init")
    
    # Push
    remotes = git_engine.remotes()
    result = remotes.push(repo, "origin", "master")
    assert result.success is True
    
    # Ls-remote
    ls_result = remotes.ls_remote(bare_repo)
    assert "refs/heads/master" in ls_result


def test_fetch_and_pull(git_engine: GitEngine, repo: Repository, bare_repo: str, tmp_path: Path) -> None:
    # First set up the bare repo with a commit by pushing from repo
    f = Path(repo.path) / "file.txt"
    f.write_text("init")
    commits = git_engine.commits()
    commits.add_all(repo)
    commits.create(repo, "init")
    
    remotes = git_engine.remotes()
    remotes.add(repo, "origin", bare_repo)
    remotes.push(repo, "origin", "master")
    
    # Now create a second clone
    clone2_path = tmp_path / "clone2"
    repo2 = git_engine.clone(bare_repo, str(clone2_path))
    
    # Update first repo and push
    f.write_text("update")
    commits.add_all(repo)
    commits.create(repo, "update")
    remotes.push(repo, "origin", "master")
    
    # Fetch and pull in second repo
    remotes2 = git_engine.remotes()
    fetch_result = remotes2.fetch(repo2, "origin")
    assert fetch_result.success is True
    
    pull_result = remotes2.pull(repo2, "origin", "master")
    assert pull_result.success is True
    assert (clone2_path / "file.txt").read_text() == "update"


def test_validator_security() -> None:
    from orbit_git.validator import GitValidator
    
    with pytest.raises(GitError, match="Embedded credentials in URLs are forbidden"):
        GitValidator.validate_url("https://user:pass@github.com/test.git")
        
    with pytest.raises(GitError, match="Embedded credentials in URLs are forbidden"):
        GitValidator.validate_url("user:pass@github.com:test.git")
        
    with pytest.raises(GitError, match="forbidden"):
        GitValidator.validate_url("ext::sh -c evil")
        
    # Valid urls
    assert GitValidator.validate_url("https://github.com/test.git")
    assert GitValidator.validate_url("git@github.com:test.git")
    assert GitValidator.validate_url("/local/path/repo.git")
