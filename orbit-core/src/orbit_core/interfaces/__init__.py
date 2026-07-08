"""ORBIT interfaces — structural typing contracts via Protocol."""

from orbit_core.interfaces.config import ConfigLoader
from orbit_core.interfaces.engine import Engine
from orbit_core.interfaces.health import HealthCheck
from orbit_core.interfaces.lifecycle import Lifecycle
from orbit_core.interfaces.logging import Logger
from orbit_core.interfaces.metrics import MetricsCollector
from orbit_core.interfaces.providers import (
    CacheProvider,
    EmbeddingProvider,
    GitProvider,
    Provider,
    SearchProvider,
    StorageProvider,
    TerminalProvider,
)
from orbit_core.interfaces.registry import Registry

__all__ = [
    "Engine",
    "HealthCheck",
    "Lifecycle",
    "Provider",
    "StorageProvider",
    "EmbeddingProvider",
    "SearchProvider",
    "CacheProvider",
    "TerminalProvider",
    "GitProvider",
    "ConfigLoader",
    "Logger",
    "MetricsCollector",
    "Registry",
]
