"""Version information for ORBIT Core."""

from __future__ import annotations

import platform
import sys
from dataclasses import dataclass, field

__version__ = "0.1.0"


@dataclass(frozen=True, slots=True)
class VersionInfo:
    """Complete version and build metadata for any ORBIT component."""

    version: str = __version__
    build: str = ""
    commit: str = ""
    branch: str = ""
    python: str = field(default_factory=lambda: f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
    platform: str = field(default_factory=platform.system)
    architecture: str = field(default_factory=lambda: platform.machine())

    def to_dict(self) -> dict[str, str]:
        """Serialize to a plain dictionary."""
        return {
            "version": self.version,
            "build": self.build,
            "commit": self.commit,
            "branch": self.branch,
            "python": self.python,
            "platform": self.platform,
            "architecture": self.architecture,
        }

    @staticmethod
    def from_environment() -> VersionInfo:
        """Create a VersionInfo populated from the current runtime environment."""
        return VersionInfo()
