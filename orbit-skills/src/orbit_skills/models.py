"""ORBIT Skills — Immutable data models and type definitions.

All models use frozen dataclasses from the standard library.
No Pydantic. No generic Dict/Any payloads.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

# --- Type Aliases ---

SkillId = str
CapabilityId = str

# --- Enumerations ---


class SkillCategory(Enum):
    """Broad classification for skill discovery and filtering."""

    ANALYSIS = "analysis"
    MODIFICATION = "modification"
    SEARCH = "search"
    AUTOMATION = "automation"


# --- Core Models ---


@dataclass(frozen=True)
class SkillCapability:
    """Declares the set of generic capabilities required by a skill."""

    required_capabilities: frozenset[CapabilityId]


@dataclass(frozen=True)
class SkillMetadata:
    """Static metadata associated with every registered Skill."""

    id: SkillId
    name: str
    description: str
    category: SkillCategory
    capabilities: SkillCapability
    version: str


# --- Input / Output Base Classes ---


@dataclass(frozen=True)
class SkillInput:
    """Base class for all skill inputs."""


@dataclass(frozen=True)
class SkillOutput:
    """Base class for all skill outputs."""


# --- Concrete Input / Output Types ---


@dataclass(frozen=True)
class RepositorySummaryInput(SkillInput):
    """Input for the Repository Summary skill."""

    repository_path: str
    include_history: bool = True


@dataclass(frozen=True)
class RepositorySummaryOutput(SkillOutput):
    """Output for the Repository Summary skill."""

    project_name: str
    commit_count: int
    summary_markdown: str


@dataclass(frozen=True)
class ReviewChangesInput(SkillInput):
    """Input for the Review Changes skill."""

    repository_path: str
    target_branch: str


@dataclass(frozen=True)
class ReviewChangesOutput(SkillOutput):
    """Output for the Review Changes skill."""

    diff_summary: str
    risk_score: float


@dataclass(frozen=True)
class ExplainCommitInput(SkillInput):
    """Input for the Explain Commit skill."""

    repository_path: str
    commit_hash: str


@dataclass(frozen=True)
class ExplainCommitOutput(SkillOutput):
    """Output for the Explain Commit skill."""

    explanation: str
    affected_files: tuple[str, ...]


@dataclass(frozen=True)
class SearchProjectInput(SkillInput):
    """Input for the Search Project skill."""

    query: str
    project_path: str


@dataclass(frozen=True)
class SearchProjectOutput(SkillOutput):
    """Output for the Search Project skill."""

    results_markdown: str
    result_count: int


# --- Error ---


@dataclass
class SkillError(Exception):
    """Standardized error raised during skill execution."""

    skill_id: SkillId
    message: str
    code: str
    details: dict[str, str] = field(default_factory=dict)

    def __str__(self) -> str:
        return f"SkillError[{self.code}] {self.skill_id}: {self.message}"


# --- Request / Result Envelopes ---


@dataclass(frozen=True)
class SkillRequest:
    """Envelope structure representing a request from a consumer."""

    skill_id: SkillId
    input_data: SkillInput
    idempotency_key: str | None = None
    timeout_ms: int | None = None


@dataclass(frozen=True)
class SkillResult:
    """Envelope structure containing the final execution output."""

    skill_id: SkillId
    success: bool
    output: SkillOutput | None = None
    error: SkillError | None = None
    duration_ms: int = 0
