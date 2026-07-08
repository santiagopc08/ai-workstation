"""Exceptions for ORBIT Execution."""

from orbit_core.exceptions.errors import OrbitError


class ExecutionError(OrbitError):
    """Base exception for all execution-related errors."""


class PolicyViolationError(ExecutionError):
    """Execution rejected due to security policy constraints."""


class SandboxViolationError(ExecutionError):
    """Execution rejected due to OS-level sandbox constraints (e.g. traversal, permissions)."""


class TimeoutError(ExecutionError):
    """Raised when an execution exceeds its allowed timeout."""
