"""Unified settings manager with layered configuration sources.

Priority: CLI → Environment → YAML → Defaults.
"""

from __future__ import annotations

import os
from typing import Any


class SettingsManager:
    """Layered configuration manager.

    Supports multiple configuration sources with well-defined
    priority: CLI args > environment variables > YAML file > defaults.
    """

    def __init__(self) -> None:
        self._defaults: dict[str, Any] = {}
        self._yaml: dict[str, Any] = {}
        self._env: dict[str, Any] = {}
        self._cli: dict[str, Any] = {}

    def set_defaults(self, values: dict[str, Any]) -> None:
        """Set default values (lowest priority)."""
        self._defaults.update(values)

    def load_dict(self, values: dict[str, Any]) -> None:
        """Load CLI-provided values (highest priority)."""
        self._cli.update(values)

    def load_env_prefix(self, prefix: str) -> None:
        """Load all environment variables matching a prefix.

        Example: prefix="ORBIT_" loads ORBIT_ROOT, ORBIT_CACHE_SIZE, etc.
        Keys are stored lowercase without the prefix.
        """
        for key, value in os.environ.items():
            if key.startswith(prefix):
                normalized = key[len(prefix):].lower()
                self._env[normalized] = value

    def load_yaml(self, path: str) -> None:
        """Load configuration from a YAML file.

        Requires pyyaml to be installed (optional dependency).
        Silently skips if the file doesn't exist or pyyaml is unavailable.
        """
        try:
            import yaml  # type: ignore[import-untyped]
        except ImportError:
            return

        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    self._yaml.update(data)
        except FileNotFoundError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value respecting the priority chain."""
        if key in self._cli:
            return self._cli[key]
        if key in self._env:
            return self._env[key]
        if key in self._yaml:
            return self._yaml[key]
        if key in self._defaults:
            return self._defaults[key]
        return default

    def set(self, key: str, value: Any) -> None:
        """Override a value at CLI priority (highest)."""
        self._cli[key] = value

    def has(self, key: str) -> bool:
        """Check if a key exists in any layer."""
        return (
            key in self._cli
            or key in self._env
            or key in self._yaml
            or key in self._defaults
        )

    def all(self) -> dict[str, Any]:
        """Return the merged configuration, respecting priority."""
        merged: dict[str, Any] = {}
        merged.update(self._defaults)
        merged.update(self._yaml)
        merged.update(self._env)
        merged.update(self._cli)
        return merged
