"""Tests for exception hierarchy."""

from orbit_core.exceptions.errors import (
    CapabilityError,
    OrbitError,
    ProviderError,
)


def test_orbit_error_base() -> None:
    err = OrbitError("base error", details="some info")
    assert str(err) == "base error"
    assert err.details == "some info"
    assert isinstance(err, Exception)


def test_hierarchy() -> None:
    err1 = ProviderError("failed")
    err2 = CapabilityError("missing")
    
    assert isinstance(err1, OrbitError)
    assert isinstance(err2, OrbitError)
