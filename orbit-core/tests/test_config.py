"""Tests for SettingsManager."""

import os
from unittest.mock import patch

from orbit_core.config.manager import SettingsManager


def test_settings_priority() -> None:
    manager = SettingsManager()
    
    manager.set_defaults({"port": 8080, "host": "localhost"})
    manager.load_dict({"port": 9090})
    
    assert manager.get("port") == 9090
    assert manager.get("host") == "localhost"
    assert manager.has("port") is True


def test_settings_env_prefix() -> None:
    manager = SettingsManager()
    with patch.dict(os.environ, {"ORBIT_API_KEY": "secret"}):
        manager.load_env_prefix("ORBIT_")
    
    assert manager.get("api_key") == "secret"


def test_settings_set() -> None:
    manager = SettingsManager()
    manager.set("foo", "bar")
    assert manager.get("foo") == "bar"


def test_settings_all() -> None:
    manager = SettingsManager()
    manager.set_defaults({"a": 1})
    manager.set("b", 2)
    assert manager.all() == {"a": 1, "b": 2}


def test_settings_yaml_missing() -> None:
    manager = SettingsManager()
    manager.load_yaml("does_not_exist.yaml")
    assert manager.all() == {}
