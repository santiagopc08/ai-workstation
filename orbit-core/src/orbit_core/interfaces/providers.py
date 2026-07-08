"""Provider protocols — structural typing contracts for all backend providers."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from orbit_core.types.models import SearchResult


@runtime_checkable
class Provider(Protocol):
    """Base provider contract."""

    @property
    def name(self) -> str:
        """Provider identifier."""
        ...

    def initialize(self) -> None:
        """Start the provider."""
        ...

    def shutdown(self) -> None:
        """Stop the provider."""
        ...


@runtime_checkable
class StorageProvider(Protocol):
    """Persistent key-value or document storage."""

    def save(self, key: str, value: Any) -> None:
        """Persist a value."""
        ...

    def load(self, key: str) -> Any:
        """Retrieve a persisted value."""
        ...

    def delete(self, key: str) -> None:
        """Remove a persisted value."""
        ...

    def exists(self, key: str) -> bool:
        """Check if a key exists."""
        ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Vector embedding computation."""

    def embed(self, text: str) -> list[float]:
        """Compute an embedding vector for a single text."""
        ...

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Compute embedding vectors for multiple texts."""
        ...


@runtime_checkable
class SearchProvider(Protocol):
    """Search index operations."""

    def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Execute a search query."""
        ...

    def index(self, key: str, content: str) -> None:
        """Index a document for future searches."""
        ...


@runtime_checkable
class CacheProvider(Protocol):
    """In-memory cache operations."""

    def get(self, key: str) -> Any | None:
        """Retrieve a cached value, or None."""
        ...

    def set(self, key: str, value: Any) -> None:
        """Store a value in the cache."""
        ...

    def clear(self) -> None:
        """Evict all cached entries."""
        ...

    def stats(self) -> dict[str, Any]:
        """Return cache hit/miss statistics."""
        ...


@runtime_checkable
class TerminalProvider(Protocol):
    """Shell command execution."""

    def execute(self, command: str, cwd: str | None = None) -> str:
        """Execute a command and return stdout."""
        ...


@runtime_checkable
class GitProvider(Protocol):
    """Git repository operations."""

    def status(self, repo_path: str) -> dict[str, Any]:
        """Return repository status."""
        ...

    def log(self, repo_path: str, limit: int = 10) -> list[dict[str, Any]]:
        """Return recent commits."""
        ...

    def diff(self, repo_path: str) -> str:
        """Return unstaged diff."""
        ...
