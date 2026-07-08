"""Lifecycle protocol — initialize/shutdown contract."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Lifecycle(Protocol):
    """Any component with a managed lifecycle."""

    def initialize(self) -> None:
        """Start up the component, acquire resources."""
        ...

    def shutdown(self) -> None:
        """Tear down the component, release resources."""
        ...
