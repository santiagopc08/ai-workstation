"""OrbitLogger — structured logging with TRACE, colored console, and JSON mode.

Never use print(). Always use get_logger().
"""

from __future__ import annotations

import json
import logging
import sys
from typing import Any

# Custom TRACE level (below DEBUG)
TRACE = 5
logging.addLevelName(TRACE, "TRACE")

# ANSI color codes for console output
_COLORS: dict[int, str] = {
    TRACE: "\033[90m",       # grey
    logging.DEBUG: "\033[36m",    # cyan
    logging.INFO: "\033[32m",     # green
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",    # red
    logging.CRITICAL: "\033[35m", # magenta
}
_RESET = "\033[0m"


class _ColorFormatter(logging.Formatter):
    """Console formatter with ANSI colors."""

    def format(self, record: logging.LogRecord) -> str:
        color = _COLORS.get(record.levelno, "")
        level = record.levelname.ljust(8)
        return f"{color}{level}{_RESET} [{record.name}] {record.getMessage()}"


class _JsonFormatter(logging.Formatter):
    """Structured JSON log formatter."""

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[1]:
            entry["exception"] = str(record.exc_info[1])
        return json.dumps(entry)


class OrbitLogger:
    """Production-grade logger wrapping stdlib logging.

    Supports TRACE, DEBUG, INFO, WARNING, ERROR, CRITICAL levels.
    Supports colored console and structured JSON output modes.
    """

    def __init__(self, name: str, *, json_mode: bool = False, level: int = logging.INFO) -> None:
        self._logger = logging.getLogger(f"orbit.{name}")
        self._logger.setLevel(level)
        self._logger.propagate = False

        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(_JsonFormatter() if json_mode else _ColorFormatter())
            self._logger.addHandler(handler)

    def trace(self, msg: str, **kwargs: Any) -> None:
        """Log at TRACE level (most verbose)."""
        self._logger.log(TRACE, msg, **kwargs)

    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log at DEBUG level."""
        self._logger.debug(msg, **kwargs)

    def info(self, msg: str, **kwargs: Any) -> None:
        """Log at INFO level."""
        self._logger.info(msg, **kwargs)

    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log at WARNING level."""
        self._logger.warning(msg, **kwargs)

    def error(self, msg: str, **kwargs: Any) -> None:
        """Log at ERROR level."""
        self._logger.error(msg, **kwargs)

    def critical(self, msg: str, **kwargs: Any) -> None:
        """Log at CRITICAL level."""
        self._logger.critical(msg, **kwargs)

    def set_level(self, level: int) -> None:
        """Change the logging level at runtime."""
        self._logger.setLevel(level)


def get_logger(name: str, *, json_mode: bool = False, level: int = logging.INFO) -> OrbitLogger:
    """Factory function — the only way to create an OrbitLogger."""
    return OrbitLogger(name, json_mode=json_mode, level=level)
