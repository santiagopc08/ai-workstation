"""Hashing utilities wrapping hashlib."""

from __future__ import annotations

import hashlib


def sha256(data: str | bytes) -> str:
    """Compute SHA-256 hex digest."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def md5(data: str | bytes) -> str:
    """Compute MD5 hex digest."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.md5(data).hexdigest()  # noqa: S324
