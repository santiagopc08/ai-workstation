"""Tests for OrbitLogger."""

import json
import logging
from io import StringIO
from unittest.mock import patch

from orbit_core.logging.logger import TRACE, OrbitLogger, get_logger


def test_get_logger() -> None:
    logger = get_logger("test")
    assert isinstance(logger, OrbitLogger)


def test_logger_levels() -> None:
    with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
        logger = get_logger("test_levels", level=TRACE)
        logger.trace("trace msg")
        logger.debug("debug msg")
        logger.info("info msg")
        logger.warning("warn msg")
        logger.error("error msg")
        logger.critical("crit msg")
        
        output = mock_stderr.getvalue()
        assert "trace msg" in output
        assert "debug msg" in output
        assert "info msg" in output
        assert "warn msg" in output
        assert "error msg" in output
        assert "crit msg" in output


def test_json_formatter() -> None:
    with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
        logger = get_logger("test_json", json_mode=True)
        logger.info("hello")
        
        output = mock_stderr.getvalue().strip()
        parsed = json.loads(output)
        
        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "orbit.test_json"
        assert parsed["message"] == "hello"


def test_set_level() -> None:
    with patch("sys.stderr", new_callable=StringIO) as mock_stderr:
        logger = get_logger("test_set", level=logging.INFO)
        logger.debug("hidden")
        
        logger.set_level(logging.DEBUG)
        logger.debug("visible")
        
        output = mock_stderr.getvalue()
        assert "hidden" not in output
        assert "visible" in output
