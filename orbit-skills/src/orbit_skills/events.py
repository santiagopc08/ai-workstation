"""ORBIT Skills — Events emitted during skill execution."""

from __future__ import annotations

from dataclasses import dataclass

from orbit_core.events import Event


@dataclass(frozen=True)
class SkillExecutionStarted(Event):
    """Published when a skill begins execution."""

    skill_id: str = ""


@dataclass(frozen=True)
class SkillExecutionCompleted(Event):
    """Published when a skill completes execution successfully."""

    skill_id: str = ""
    duration_ms: int = 0
    success: bool = True
    capabilities_resolved: tuple[str, ...] = ()
    tokens_sent: int = 0
    tokens_received: int = 0


@dataclass(frozen=True)
class SkillExecutionFailed(Event):
    """Published when a skill execution fails."""

    skill_id: str = ""
    error: str = ""
    duration_ms: int = 0
