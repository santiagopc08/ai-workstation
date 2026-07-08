"""Strict exception hierarchy for the ORBIT platform.

Every error raised by any ORBIT component MUST extend OrbitError.
Never raise bare Exception.
"""

from __future__ import annotations


class OrbitError(Exception):
    """Base exception for all ORBIT platform errors."""

    def __init__(self, message: str = "", *, details: str = "") -> None:
        self.details = details
        super().__init__(message)


class ConfigurationError(OrbitError):
    """Raised when configuration is invalid, missing, or malformed."""


class ProviderError(OrbitError):
    """Raised when a provider fails to initialize or operate."""


class ValidationError(OrbitError):
    """Raised when input data fails validation rules."""


class CapabilityError(OrbitError):
    """Raised when a capability cannot be registered, resolved, or executed."""


class StorageError(OrbitError):
    """Raised when a storage backend operation fails."""


class SearchError(OrbitError):
    """Raised when a search operation fails."""


class EmbeddingError(OrbitError):
    """Raised when an embedding computation or retrieval fails."""


class ToolError(OrbitError):
    """Raised when an MCP tool invocation fails."""


class HealthError(OrbitError):
    """Raised when a health check fails or returns an unhealthy state."""
