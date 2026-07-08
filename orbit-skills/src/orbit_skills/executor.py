"""ORBIT Skills — Skill Executor.

Implements the complete execution flow:
SkillRequest → SkillValidator → SkillContext → Skill → SkillResult → Observability
"""

from __future__ import annotations

import time

from orbit_core.logging import get_logger

from orbit_skills.context import OrbitSkillContext
from orbit_skills.events import SkillExecutionCompleted, SkillExecutionFailed, SkillExecutionStarted
from orbit_skills.models import SkillError, SkillRequest, SkillResult
from orbit_skills.registry import SkillRegistry, SkillValidator

_log = get_logger("skills.executor")


class SkillExecutor:
    """Entry point for consumers to invoke a skill securely.

    Wraps execution with timing, structured logging, and event emission.
    """

    def __init__(self, registry: SkillRegistry, context: OrbitSkillContext) -> None:
        self._registry = registry
        self._context = context
        self._validator = SkillValidator(registry, context)

    def execute(self, request: SkillRequest) -> SkillResult:
        """Validate the request, provision the context, and execute the skill."""
        start = time.monotonic()

        # Emit start event
        self._context.events.publish(
            SkillExecutionStarted(skill_id=request.skill_id, source="SkillExecutor")
        )
        _log.info(f"Executing skill: {request.skill_id}")

        try:
            # Validate
            skill = self._validator.validate(request)

            # Execute
            output = skill.execute(request.input_data, self._context)

            duration_ms = int((time.monotonic() - start) * 1000)

            # Emit completion event
            capabilities = tuple(skill.metadata.capabilities.required_capabilities)
            self._context.events.publish(
                SkillExecutionCompleted(
                    skill_id=request.skill_id,
                    duration_ms=duration_ms,
                    success=True,
                    capabilities_resolved=capabilities,
                    source="SkillExecutor",
                )
            )
            _log.info(f"Skill completed: {request.skill_id} ({duration_ms}ms)")

            return SkillResult(
                skill_id=request.skill_id,
                success=True,
                output=output,
                duration_ms=duration_ms,
            )

        except SkillError as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._context.events.publish(
                SkillExecutionFailed(
                    skill_id=request.skill_id,
                    error=str(e),
                    duration_ms=duration_ms,
                    source="SkillExecutor",
                )
            )
            _log.error(f"Skill failed: {request.skill_id} — {e}")
            return SkillResult(
                skill_id=request.skill_id,
                success=False,
                error=e,
                duration_ms=duration_ms,
            )

        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            error = SkillError(
                skill_id=request.skill_id,
                message=str(e),
                code="EXECUTION_ERROR",
            )
            self._context.events.publish(
                SkillExecutionFailed(
                    skill_id=request.skill_id,
                    error=str(e),
                    duration_ms=duration_ms,
                    source="SkillExecutor",
                )
            )
            _log.error(f"Skill error: {request.skill_id} — {e}")
            return SkillResult(
                skill_id=request.skill_id,
                success=False,
                error=error,
                duration_ms=duration_ms,
            )
