"""Safe path manipulation utilities."""

from __future__ import annotations

import os


def normalize(path: str) -> str:
    """Normalize a path to its absolute, resolved form."""
    return os.path.normpath(os.path.abspath(path))


def safe_join(base: str, *parts: str) -> str:
    """Join paths and verify the result stays inside the base.

    Raises ValueError if the resulting path escapes the base directory.
    """
    resolved = normalize(os.path.join(base, *parts))
    base_resolved = normalize(base)
    if not resolved.startswith(base_resolved + os.sep) and resolved != base_resolved:
        raise ValueError(f"Path traversal detected: {resolved} escapes {base_resolved}")
    return resolved


def is_inside(path: str, base: str) -> bool:
    """Check if a path is inside a base directory."""
    resolved = normalize(path)
    base_resolved = normalize(base)
    return resolved.startswith(base_resolved + os.sep) or resolved == base_resolved
