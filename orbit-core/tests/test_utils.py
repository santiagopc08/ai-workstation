"""Tests for shared utilities."""


import pytest

from orbit_core.exceptions.errors import ValidationError
from orbit_core.utils.hashing import md5, sha256
from orbit_core.utils.lazy import LazyLoader
from orbit_core.utils.paths import is_inside, normalize, safe_join
from orbit_core.utils.retry import retry
from orbit_core.utils.timing import Stopwatch, Timer
from orbit_core.utils.validation import require, require_not_none


def test_hashing() -> None:
    assert len(sha256("test")) == 64
    assert len(md5(b"test")) == 32


def test_paths() -> None:
    base = "/opt/orbit"
    assert normalize("/opt/orbit/../orbit") == "/opt/orbit"
    assert safe_join(base, "data/db.sqlite") == "/opt/orbit/data/db.sqlite"
    
    with pytest.raises(ValueError):
        safe_join(base, "../etc/passwd")
        
    assert is_inside("/opt/orbit/data", base) is True
    assert is_inside("/opt", base) is False


def test_validation() -> None:
    require(True)
    with pytest.raises(ValidationError):
        require(False)
        
    assert require_not_none("test") == "test"
    with pytest.raises(ValidationError):
        require_not_none(None)


def test_lazy_loader() -> None:
    calls = 0
    
    def factory() -> int:
        nonlocal calls
        calls += 1
        return 42
        
    loader = LazyLoader(factory)
    assert loader.is_initialized is False
    
    assert loader.get() == 42
    assert loader.is_initialized is True
    assert calls == 1
    
    assert loader.get() == 42
    assert calls == 1
    
    loader.reset()
    assert loader.is_initialized is False
    assert loader.get() == 42
    assert calls == 2


def test_timing() -> None:
    with Timer() as t:
        pass
    assert t.elapsed >= 0
    assert t.elapsed_ms >= 0

    sw = Stopwatch()
    sw.start()
    sw.lap()
    sw.stop()
    assert sw.elapsed >= 0
    assert len(sw.laps) == 1


def test_retry() -> None:
    calls = 0
    
    @retry(max_attempts=3, backoff=0.01)
    def flaky() -> int:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError("fail")
        return 42
        
    assert flaky() == 42
    assert calls == 3
