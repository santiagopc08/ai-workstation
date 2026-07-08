"""Immutable, shared data models for the ORBIT platform.

All models use frozen dataclasses with slots for memory efficiency
and immutability guarantees across engine boundaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Document:
    """A knowledge document within the platform."""

    path: str
    title: str
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Chunk:
    """A fragment of a document optimized for RAG and embedding."""

    id: str
    document: str
    section: str
    title: str
    text: str
    hash: str
    start_line: int = 0
    end_line: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A scored match returned by a search provider."""

    file: str
    line: int
    text: str
    score: float

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "file": self.file,
            "line": self.line,
            "text": self.text,
            "score": round(self.score, 4),
        }


@dataclass(frozen=True, slots=True)
class Embedding:
    """A vector embedding with associated metadata."""

    id: str
    vector: list[float] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Project:
    """A logical project grouping within the knowledge base."""

    name: str
    root: str
    files_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CapabilityInfo:
    """Describes a registered capability."""

    id: str
    name: str
    version: str
    status: str = "unknown"


@dataclass(frozen=True, slots=True)
class HealthStatus:
    """Health check result for an engine or provider."""

    status: str
    version: str = ""
    uptime: float = 0.0
    dependencies: dict[str, str] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ProviderInfo:
    """Describes a registered provider."""

    name: str
    type: str
    version: str = ""
    healthy: bool = True


@dataclass(frozen=True, slots=True)
class EngineInfo:
    """Describes an engine and its capabilities."""

    name: str
    version: str
    capabilities: list[str] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class ToolInfo:
    """Describes an MCP tool."""

    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
