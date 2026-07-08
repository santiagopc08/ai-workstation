"""Minimalist dependency injection container.

Register. Resolve. Nothing more. No frameworks.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Callable, TypeVar, cast

from orbit_core.exceptions.errors import ProviderError

T = TypeVar("T")


class Container:
    """Extremely small DI container.

    Supports both instance registration and factory registration.
    Factories are called once on first resolve (lazy singleton).
    """

    def __init__(self) -> None:
        self._instances: dict[type[Any], Any] = {}
        self._factories: dict[type[Any], Callable[[], Any]] = {}

    def register_instance(self, interface: type[T], instance: T) -> None:
        """Register a concrete instance for an interface."""
        self._instances[interface] = instance

    def register_factory(self, interface: type[T], factory: Callable[[], T]) -> None:
        """Register a factory that will be called once on first resolve."""
        self._factories[interface] = factory

    def resolve(self, interface: type[T]) -> T:
        """Resolve an interface to its implementation.

        If a factory was registered, it is called once and the result cached.
        Raises ProviderError if no registration exists.
        """
        if interface in self._instances:
            return cast(T, self._instances[interface])

        if interface in self._factories:
            instance = self._factories.pop(interface)()
            self._instances[interface] = instance
            return cast(T, instance)

        raise ProviderError(f"No registration for: {interface.__name__}")

    def has(self, interface: type[Any]) -> bool:
        """Check if an interface has been registered."""
        return interface in self._instances or interface in self._factories

    def clear(self) -> None:
        """Remove all registrations."""
        self._instances.clear()
        self._factories.clear()
