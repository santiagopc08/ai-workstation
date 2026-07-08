"""Search Project Skill — Searches a project using Knowledge."""

from __future__ import annotations

from orbit_core.logging import get_logger

from orbit_skills.context import OrbitSkillContext
from orbit_skills.models import (
    SearchProjectInput,
    SearchProjectOutput,
    SkillCapability,
    SkillCategory,
    SkillInput,
    SkillMetadata,
    SkillOutput,
)

_log = get_logger("skills.search_project")


class SearchProjectSkill:
    """Searches a project's knowledge base."""

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            id="orbit.search.project",
            name="Search Project",
            description="Searches a project's knowledge base for relevant information.",
            category=SkillCategory.SEARCH,
            capabilities=SkillCapability(
                required_capabilities=frozenset({
                    "knowledge.search",
                })
            ),
            version="0.1.0",
        )

    def execute(self, input_data: SkillInput, context: OrbitSkillContext) -> SkillOutput:
        """Execute the search project skill."""
        assert isinstance(input_data, SearchProjectInput)

        knowledge_svc = context.resolve("knowledge.search")

        _log.info(f"Searching project: {input_data.query}")

        try:
            results = knowledge_svc.related_knowledge(None, input_data.query)
            output_parts = [f"# Search Results: {input_data.query}", ""]
            for r in results:
                output_parts.append(f"- {r}")

            return SearchProjectOutput(
                results_markdown="\n".join(output_parts),
                result_count=len(results),
            )
        except Exception:
            return SearchProjectOutput(
                results_markdown=f"# Search Results: {input_data.query}\n\nNo results found.",
                result_count=0,
            )
