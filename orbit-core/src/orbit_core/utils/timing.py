"""Timing utilities — Timer context manager and Stopwatch."""

from __future__ import annotations

import time


class Timer:
    """Context manager that measures elapsed wall-clock time.

    Usage:
        with Timer() as t:
            do_work()
        print(t.elapsed_ms)
    """

    def __init__(self) -> None:
        self._start: float = 0.0
        self._end: float = 0.0

    def __enter__(self) -> Timer:
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        self._end = time.perf_counter()

    @property
    def elapsed(self) -> float:
        """Elapsed time in seconds."""
        end = self._end if self._end else time.perf_counter()
        return end - self._start

    @property
    def elapsed_ms(self) -> float:
        """Elapsed time in milliseconds."""
        return self.elapsed * 1000


class Stopwatch:
    """Manual start/stop/lap stopwatch.

    Usage:
        sw = Stopwatch()
        sw.start()
        sw.lap()  # records a lap
        sw.stop()
        print(sw.elapsed_ms)
    """

    def __init__(self) -> None:
        self._start: float = 0.0
        self._end: float = 0.0
        self._laps: list[float] = []
        self._running: bool = False

    def start(self) -> None:
        """Start the stopwatch."""
        self._start = time.perf_counter()
        self._end = 0.0
        self._running = True

    def stop(self) -> None:
        """Stop the stopwatch."""
        self._end = time.perf_counter()
        self._running = False

    def lap(self) -> float:
        """Record a lap and return its duration in seconds."""
        now = time.perf_counter()
        last = self._laps[-1] if self._laps else self._start
        duration = now - last
        self._laps.append(now)
        return duration

    @property
    def elapsed(self) -> float:
        """Total elapsed time in seconds."""
        end = self._end if not self._running else time.perf_counter()
        return end - self._start

    @property
    def elapsed_ms(self) -> float:
        """Total elapsed time in milliseconds."""
        return self.elapsed * 1000

    @property
    def laps(self) -> list[float]:
        """Return a copy of all recorded lap timestamps."""
        return list(self._laps)
