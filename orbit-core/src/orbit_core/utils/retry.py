"""Retry with exponential backoff."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")


def retry(
    *,
    max_attempts: int = 3,
    backoff: float = 0.1,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator / wrapper that retries a function with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (default 3).
        backoff: Initial delay in seconds between retries (default 0.1).
        exceptions: Tuple of exception types to catch.

    Returns:
        A wrapped function that retries on failure.
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        def wrapper(*args: Any, **kwargs: Any) -> T:
            delay = backoff
            last_exception: BaseException | None = None
            for attempt in range(max_attempts):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                        delay *= 2
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator
