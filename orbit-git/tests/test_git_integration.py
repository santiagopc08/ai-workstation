"""Tests for ORBIT Git x Knowledge Integration (Sprint 5)."""

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from orbit_core.events import EventBus
from orbit_execution import ExecutionEngine

from orbit_git import GitEngine, Repository
from orbit_git.integration import GitKnowledgeService


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


@patch("orbit_git.integration.summarize_document")
def test_summarize_diff(mock_summarize_document: Any, git_engine: GitEngine, repo: Repository, tmp_path: Path) -> None:
    mock_summarize_document.return_value = "Mocked document summary."
    
    svc = GitKnowledgeService(git_engine)
    
    f = tmp_path / "test.txt"
    f.write_text("hello\n")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "commit 1")
    
    f.write_text("hello\nworld\n")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "commit 2")
    
    history = git_engine.history().log(repo)
    ref_b = history[0].hash
    ref_a = history[1].hash
    
    summary = svc.summarize_diff(repo, ref_a, ref_b)
    
    assert "Diff Summary" in summary
    assert "**Files changed:**" in summary
    assert "test.txt" in summary
    assert "Mocked document summary." in summary


@patch("orbit_git.integration.summarize_document")
def test_summarize_commit(mock_summarize_document: Any, git_engine: GitEngine, repo: Repository, tmp_path: Path) -> None:
    mock_summarize_document.return_value = "Mocked commit doc summary."
    
    svc = GitKnowledgeService(git_engine)
    
    (tmp_path / "init.txt").write_text("init")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "init")
    
    f = tmp_path / "test2.txt"
    f.write_text("test2\n")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "feat: add test2")
    
    history = git_engine.history().log(repo)
    commit_hash = history[0].hash
    
    summary = svc.summarize_commit(repo, commit_hash)
    
    assert "Commit Summary" in summary
    assert "feat: add test2" in summary
    assert "test2.txt" in summary
    assert "Mocked commit doc summary." in summary


def test_summarize_history(git_engine: GitEngine, repo: Repository, tmp_path: Path) -> None:
    svc = GitKnowledgeService(git_engine)
    
    f = tmp_path / "test3.txt"
    f.write_text("test3\n")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "commit A")
    (tmp_path / "test4.txt").write_text("4")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "commit B")
    (tmp_path / "test5.txt").write_text("5")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "commit C")
    
    summary = svc.summarize_history(repo, limit=2)
    
    assert "History Summary" in summary
    assert "commit C" in summary
    assert "commit B" in summary
    assert "commit A" not in summary


@patch("orbit_git.integration.related_documents")
def test_affected_documents(mock_related_documents: Any, git_engine: GitEngine, repo: Repository, tmp_path: Path) -> None:
    mock_related_documents.return_value = ["docs/architecture.md"]
    
    svc = GitKnowledgeService(git_engine)
    
    (tmp_path / "init.txt").write_text("init")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "init")
    
    f = tmp_path / "src.py"
    f.write_text("print('hello')\n")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "add src")
    
    history = git_engine.history().log(repo)
    commit_hash = history[0].hash
    
    affected = svc.affected_documents(repo, commit_hash)
    assert len(affected) == 2
    assert "docs/architecture.md" in affected
    assert "src.py" in affected


@patch("orbit_git.integration.related_documents")
def test_related_knowledge(mock_related_documents: Any, git_engine: GitEngine, repo: Repository) -> None:
    mock_related_documents.return_value = ["docs/design.md"]
    svc = GitKnowledgeService(git_engine)
    
    related = svc.related_knowledge(repo, "src.py")
    assert len(related) == 1
    assert "docs/design.md" in related


@patch("orbit_git.integration.project_metadata")
@patch("orbit_git.integration.project_summary")
def test_repository_summary(
    mock_summary: Any, mock_metadata: Any, git_engine: GitEngine, repo: Repository, tmp_path: Path
) -> None:
    mock_summary.return_value = "Mocked project summary."
    mock_metadata.return_value = {"tags": ["python", "git"]}
    
    svc = GitKnowledgeService(git_engine)
    
    (tmp_path / "init.txt").write_text("init")
    git_engine.commits().add_all(repo)
    git_engine.commits().create(repo, "init")
    
    summary = svc.repository_summary(repo, "orbit-git")
    
    assert "Repository Integration Summary: orbit-git" in summary
    assert "Mocked project summary." in summary
    assert "- **tags:** ['python', 'git']" in summary
    assert "init" in summary
