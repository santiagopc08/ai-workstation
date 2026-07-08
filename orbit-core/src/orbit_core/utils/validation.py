"""Input validation helpers."""

from __future__ import annotations

from typing import TypeVar

from orbit_core.exceptions.errors import ValidationError

T = TypeVar("T")


def require(condition: bool, message: str = "Validation failed") -> None:
    """Assert a condition, raising ValidationError if false."""
    if not condition:
        raise ValidationError(message)


def require_not_none(value: T | None, name: str = "value") -> T:
    """Assert a value is not None, returning it typed if valid."""
    if value is None:
        raise ValidationError(f"{name} must not be None")
    return value
