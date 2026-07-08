"""ORBIT Skills — Registry and Validator."""

from __future__ import annotations

from typing import Protocol

from orbit_core.logging import get_logger

from orbit_skills.context import OrbitSkillContext
from orbit_skills.models import (
    SkillCategory,
    SkillError,
    SkillId,
    SkillInput,
    SkillMetadata,
    SkillOutput,
    SkillRequest,
)

_log = get_logger("skills.registry")


class ISkill(Protocol):
    """Core interface that every skill must implement."""

    @property
    def metadata(self) -> SkillMetadata: ...

    def execute(self, input_data: SkillInput, context: OrbitSkillContext) -> SkillOutput: ...


class SkillRegistry:
    """Central repository for all available skills.

    Implements ISkillRegistry from the frozen architecture.
    """

    def __init__(self) -> None:
        self._skills: dict[SkillId, ISkill] = {}

    def register(self, skill: ISkill) -> None:
        """Register a skill in the registry."""
        skill_id = skill.metadata.id
        if skill_id in self._skills:
            raise SkillError(
                skill_id=skill_id,
                message=f"Skill already registered: {skill_id}",
                code="DUPLICATE_SKILL",
            )
        self._skills[skill_id] = skill
        _log.info(f"Skill registered: {skill_id} ({skill.metadata.name})")

    def get(self, skill_id: SkillId) -> ISkill:
        """Retrieve a skill by its ID."""
        if skill_id not in self._skills:
            raise SkillError(
                skill_id=skill_id,
                message=f"Skill not found: {skill_id}",
                code="SKILL_NOT_FOUND",
            )
        return self._skills[skill_id]

    def list_skills(self, category: SkillCategory | None = None) -> list[SkillMetadata]:
        """List all registered skills, optionally filtered by category."""
        skills = list(self._skills.values())
        if category is not None:
            skills = [s for s in skills if s.metadata.category == category]
        return [s.metadata for s in skills]

    @property
    def skill_count(self) -> int:
        """Number of registered skills."""
        return len(self._skills)


class SkillValidator:
    """Pre-execution interceptor that validates requests."""

    def __init__(self, registry: SkillRegistry, context: OrbitSkillContext) -> None:
        self._registry = registry
        self._context = context

    def validate(self, request: SkillRequest) -> ISkill:
        """Validate a request and return the resolved skill.

        Raises SkillError if validation fails.
        """
        # 1. Resolve the skill
        skill = self._registry.get(request.skill_id)

        # 2. Verify all required capabilities are available
        for cap_id in skill.metadata.capabilities.required_capabilities:
            if not self._context._registry.has(cap_id):
                raise SkillError(
                    skill_id=request.skill_id,
                    message=f"Required capability not available: {cap_id}",
                    code="CAPABILITY_UNAVAILABLE",
                )

        _log.info(f"Validated request for skill: {request.skill_id}")
        return skill
