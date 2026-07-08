"""Tests for ORBIT Git Sprint 4 (Diff & History)."""

import subprocess
from pathlib import Path

import pytest
from orbit_core.events import EventBus
from orbit_execution import ExecutionEngine

from orbit_git import GitEngine, Repository
from orbit_git.events import (
    BlameCompleted,
    DiffGenerated,
    GitEvent,
    HistoryLoaded,
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


def test_diff_manager(git_engine: GitEngine, repo: Repository, tmp_path: Path, event_bus: EventBus) -> None:
    events: list[GitEvent] = []
    event_bus.subscribe(DiffGenerated, lambda e: events.append(e))
    
    diff_mgr = git_engine.diff()
    
    # Clean diff
    d = diff_mgr.diff_working_tree(repo)
    assert d.stats.files_changed == 0
    assert len(d.files) == 0
    
    # Create file
    f = tmp_path / "test.txt"
    f.write_text("hello\nworld\n")
    
    # Untracked files aren't in diff usually, so add it
    git_engine.commits().add_all(repo)
    d = diff_mgr.diff_staged(repo)
    assert d.stats.files_changed == 1
    assert d.stats.insertions == 2
    assert len(d.files) == 1
    assert d.files[0].path == "test.txt"
    assert d.files[0].status == "A"
    
    # Commit it
    git_engine.commits().create(repo, "initial commit")
    
    # Modify file
    f.write_text("hello\nworld\nfoo\n")
    d = diff_mgr.diff_working_tree(repo)
    assert d.stats.files_changed == 1
    assert d.stats.insertions == 1
    assert d.stats.deletions == 0
    
    # diff stat
    d_stat = diff_mgr.diff_stat(repo)
    assert d_stat.files_changed == 1
    
    # Commit again
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "second commit")
    
    # diff between
    history = git_engine.history().log(repo)
    assert len(history) == 2
    ref_a = history[1].hash  # older commit
    ref_b = history[0].hash  # newer commit
    
    d = diff_mgr.diff_between(repo, ref_a, ref_b)
    assert d.stats.files_changed == 1
    
    assert len(events) >= 4


def test_history_manager(git_engine: GitEngine, repo: Repository, tmp_path: Path, event_bus: EventBus) -> None:
    events: list[GitEvent] = []
    event_bus.subscribe(HistoryLoaded, lambda e: events.append(e))
    event_bus.subscribe(BlameCompleted, lambda e: events.append(e))
    
    hist_mgr = git_engine.history()
    
    f = tmp_path / "file.txt"
    f.write_text("line 1\n")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "commit 1")
    
    f.write_text("line 1\nline 2\n")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "commit 2")
    
    f.write_text("line 1\nline 2\nline 3\n")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "commit 3")
    
    # log
    commits = hist_mgr.log(repo)
    assert len(commits) == 3
    assert commits[0].message == "commit 3"
    assert commits[1].message == "commit 2"
    assert commits[2].message == "commit 1"
    
    # show
    commit, d = hist_mgr.show(repo, commits[0].hash)
    assert commit.hash == commits[0].hash
    assert d.stats.files_changed == 1
    assert d.stats.insertions == 1
    
    # blame
    blame_lines = hist_mgr.blame(repo, "file.txt")
    assert len(blame_lines) == 3
    assert blame_lines[0].content == "line 1"
    assert blame_lines[0].commit_hash == commits[2].hash
    assert blame_lines[1].content == "line 2"
    assert blame_lines[1].commit_hash == commits[1].hash
    assert blame_lines[2].content == "line 3"
    assert blame_lines[2].commit_hash == commits[0].hash
    
    # parents
    parents = hist_mgr.parents(repo, commits[0].hash)
    assert len(parents) == 1
    assert parents[0] == commits[1].hash
    
    # children
    children = hist_mgr.children(repo, commits[2].hash)
    assert len(children) == 1
    assert children[0] == commits[1].hash
