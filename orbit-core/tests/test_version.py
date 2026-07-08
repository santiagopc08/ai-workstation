"""Tests for VersionInfo."""

from orbit_core.version import VersionInfo


def test_version_info() -> None:
    v = VersionInfo.from_environment()
    assert v.version != ""
    assert v.python != ""
    assert v.platform != ""
    
    d = v.to_dict()
    assert d["version"] == v.version
    assert d["python"] == v.python
