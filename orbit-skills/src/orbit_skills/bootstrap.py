"""ORBIT Skills — Runtime Bootstrap.

Initializes all engines, registers capabilities, registers skills,
and returns a fully configured SkillExecutor.
"""

from __future__ import annotations

from orbit_core.events import EventBus
from orbit_core.health import HealthChecker
from orbit_core.logging import get_logger
from orbit_execution import ExecutionEngine
from orbit_git import GitEngine
from orbit_git.integration import GitKnowledgeService

from orbit_skills.context import CapabilityRegistry, OrbitSkillContext
from orbit_skills.executor import SkillExecutor
from orbit_skills.llm import LLMClient, LLMConfig
from orbit_skills.registry import SkillRegistry
from orbit_skills.skills import (
    ExplainCommitSkill,
    RepositorySummarySkill,
    ReviewChangesSkill,
    SearchProjectSkill,
)

_log = get_logger("skills.bootstrap")


class OrbitBootstrap:
    """Bootstraps the entire ORBIT runtime and returns a configured SkillExecutor."""

    def __init__(self, llm_config: LLMConfig | None = None) -> None:
        self._llm_config = llm_config or LLMConfig()
        self._event_bus: EventBus | None = None
        self._executor: SkillExecutor | None = None
        self._llm_client: LLMClient | None = None

    def bootstrap(self) -> SkillExecutor:
        """Initialize all components and return a fully configured SkillExecutor."""
        _log.info("Bootstrapping ORBIT runtime...")

        # 1. Core infrastructure
        self._event_bus = EventBus()

        # 2. Engines
        execution_engine = ExecutionEngine()
        git_engine = GitEngine(execution_engine, self._event_bus)
        knowledge_svc = GitKnowledgeService(git_engine)

        # 3. LLM Client
        self._llm_client = LLMClient(self._llm_config)

        # 4. Register capabilities
        capabilities = CapabilityRegistry()
        capabilities.register("git.repository.read", git_engine)
        capabilities.register("git.history.read", git_engine)
        capabilities.register("git.diff.read", git_engine)
        capabilities.register("knowledge.summary", knowledge_svc)
        capabilities.register("knowledge.search", knowledge_svc)
        capabilities.register("llm.complete", self._llm_client)

        # 5. Build context
        context = OrbitSkillContext(capabilities, self._event_bus)

        # 6. Register skills
        registry = SkillRegistry()
        registry.register(RepositorySummarySkill())
        registry.register(ReviewChangesSkill())
        registry.register(ExplainCommitSkill())
        registry.register(SearchProjectSkill())

        # 7. Health check
        HealthChecker()
        _log.info(f"Skills registered: {registry.skill_count}")
        _log.info(f"Capabilities registered: {len(capabilities.list_capabilities())}")

        # 8. Build executor
        self._executor = SkillExecutor(registry, context)

        _log.info("ORBIT runtime bootstrapped successfully.")
        return self._executor

    def shutdown(self) -> None:
        """Clean up resources."""
        if self._llm_client:
            self._llm_client.close()
        _log.info("ORBIT runtime shut down.")
