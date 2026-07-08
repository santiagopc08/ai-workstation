"""ORBIT exception hierarchy — all platform errors extend OrbitError."""

from orbit_core.exceptions.errors import (
    CapabilityError,
    ConfigurationError,
    EmbeddingError,
    HealthError,
    OrbitError,
    ProviderError,
    SearchError,
    StorageError,
    ToolError,
    ValidationError,
)

__all__ = [
    "OrbitError",
    "ConfigurationError",
    "ProviderError",
    "ValidationError",
    "CapabilityError",
    "StorageError",
    "SearchError",
    "EmbeddingError",
    "ToolError",
    "HealthError",
]
