"""ORBIT Skills — End-to-End Integration Tests.

Uses real Git operations (no mocks).
Uses real Knowledge (no mocks).
Mocks ONLY the LLM response.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from orbit_core.events import EventBus
from orbit_execution import ExecutionEngine
from orbit_git import GitEngine
from orbit_git.integration import GitKnowledgeService

from orbit_skills.context import CapabilityRegistry, OrbitSkillContext
from orbit_skills.events import SkillExecutionCompleted, SkillExecutionStarted
from orbit_skills.executor import SkillExecutor
from orbit_skills.llm import LLMResponse
from orbit_skills.models import (
    ExplainCommitInput,
    ExplainCommitOutput,
    RepositorySummaryInput,
    RepositorySummaryOutput,
    SkillRequest,
)
from orbit_skills.registry import SkillRegistry
from orbit_skills.skills import ExplainCommitSkill, RepositorySummarySkill


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """Create a real temporary Git repository with commits."""
    repo = tmp_path
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@orbit.dev"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "ORBIT Test"], cwd=repo, check=True, capture_output=True)

    # Create initial commit
    (repo / "README.md").write_text("# Test Project\nA test repository.\n")
    subprocess.run(["git", "add", "--all"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat: initial commit"], cwd=repo, check=True, capture_output=True)

    # Create second commit
    (repo / "src.py").write_text("def hello():\n    return 'world'\n")
    subprocess.run(["git", "add", "--all"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "feat: add hello function"], cwd=repo, check=True, capture_output=True)

    # Create third commit
    (repo / "tests.py").write_text("from src import hello\nassert hello() == 'world'\n")
    subprocess.run(["git", "add", "--all"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "test: add hello test"], cwd=repo, check=True, capture_output=True)

    return repo


@pytest.fixture
def mock_llm() -> MagicMock:
    """Create a mock LLM client that returns a canned response."""
    client = MagicMock()
    client.complete.return_value = LLMResponse(
        content="# Repository Summary\n\nThis is a test project with a hello function and unit tests.\n\n"
        "## Components\n- `src.py`: Core hello function\n- `tests.py`: Unit tests\n\n"
        "## Technologies\n- Python\n- Git",
        tokens_sent=150,
        tokens_received=80,
    )
    return client


@pytest.fixture
def executor(tmp_repo: Path, mock_llm: MagicMock) -> SkillExecutor:
    """Create a fully configured SkillExecutor with real Git and mocked LLM."""
    event_bus = EventBus()
    execution_engine = ExecutionEngine()
    git_engine = GitEngine(execution_engine, event_bus)
    knowledge_svc = GitKnowledgeService(git_engine)

    capabilities = CapabilityRegistry()
    capabilities.register("git.repository.read", git_engine)
    capabilities.register("git.history.read", git_engine)
    capabilities.register("git.diff.read", git_engine)
    capabilities.register("knowledge.summary", knowledge_svc)
    capabilities.register("knowledge.search", knowledge_svc)
    capabilities.register("llm.complete", mock_llm)

    context = OrbitSkillContext(capabilities, event_bus)

    registry = SkillRegistry()
    registry.register(RepositorySummarySkill())
    registry.register(ExplainCommitSkill())

    return SkillExecutor(registry, context)


def test_repository_summary_e2e(executor: SkillExecutor, tmp_repo: Path) -> None:
    """Full end-to-end: bootstrap → executor → RepositorySummary → result."""
    request = SkillRequest(
        skill_id="orbit.repository.summary",
        input_data=RepositorySummaryInput(repository_path=str(tmp_repo)),
    )

    result = executor.execute(request)

    assert result.success is True
    assert result.duration_ms >= 0
    assert result.output is not None
    assert isinstance(result.output, RepositorySummaryOutput)
    assert result.output.commit_count == 3
    assert "Repository Summary" in result.output.summary_markdown
    assert "hello" in result.output.summary_markdown


def test_explain_commit_e2e(executor: SkillExecutor, tmp_repo: Path, mock_llm: MagicMock) -> None:
    """Full end-to-end: bootstrap → executor → ExplainCommit → result."""
    # Get latest commit hash
    git_engine = GitEngine(ExecutionEngine(), EventBus())
    repo = git_engine.open(str(tmp_repo))
    commits = git_engine.history().log(repo)
    latest_hash = commits[0].hash

    mock_llm.complete.return_value = LLMResponse(
        content="This commit adds unit tests for the hello function.",
        tokens_sent=100,
        tokens_received=50,
    )

    request = SkillRequest(
        skill_id="orbit.explain.commit",
        input_data=ExplainCommitInput(repository_path=str(tmp_repo), commit_hash=latest_hash),
    )

    result = executor.execute(request)

    assert result.success is True
    assert result.output is not None
    assert isinstance(result.output, ExplainCommitOutput)
    assert "tests" in result.output.explanation.lower()
    assert len(result.output.affected_files) > 0


def test_skill_not_found(executor: SkillExecutor) -> None:
    """Test that requesting a non-existent skill fails gracefully."""
    request = SkillRequest(
        skill_id="orbit.nonexistent.skill",
        input_data=RepositorySummaryInput(repository_path="/tmp/fake"),
    )

    result = executor.execute(request)

    assert result.success is False
    assert result.error is not None
    assert result.error.code == "SKILL_NOT_FOUND"


def test_events_emitted(tmp_repo: Path, mock_llm: MagicMock) -> None:
    """Test that execution events are properly emitted."""
    event_bus = EventBus()
    events_received: list[Any] = []

    event_bus.subscribe(SkillExecutionStarted, lambda e: events_received.append(e))
    event_bus.subscribe(SkillExecutionCompleted, lambda e: events_received.append(e))

    execution_engine = ExecutionEngine()
    git_engine = GitEngine(execution_engine, event_bus)
    knowledge_svc = GitKnowledgeService(git_engine)

    capabilities = CapabilityRegistry()
    capabilities.register("git.repository.read", git_engine)
    capabilities.register("git.history.read", git_engine)
    capabilities.register("git.diff.read", git_engine)
    capabilities.register("knowledge.summary", knowledge_svc)
    capabilities.register("knowledge.search", knowledge_svc)
    capabilities.register("llm.complete", mock_llm)

    context = OrbitSkillContext(capabilities, event_bus)
    registry = SkillRegistry()
    registry.register(RepositorySummarySkill())
    executor = SkillExecutor(registry, context)

    request = SkillRequest(
        skill_id="orbit.repository.summary",
        input_data=RepositorySummaryInput(repository_path=str(tmp_repo)),
    )

    executor.execute(request)

    assert len(events_received) == 2
    assert isinstance(events_received[0], SkillExecutionStarted)
    assert isinstance(events_received[1], SkillExecutionCompleted)
    assert events_received[1].skill_id == "orbit.repository.summary"
    assert events_received[1].duration_ms >= 0
