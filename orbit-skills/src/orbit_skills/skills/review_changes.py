"""Review Changes Skill — Analyzes a diff between branches."""

from __future__ import annotations

from orbit_core.logging import get_logger

from orbit_skills.context import OrbitSkillContext
from orbit_skills.models import (
    ReviewChangesInput,
    ReviewChangesOutput,
    SkillCapability,
    SkillCategory,
    SkillInput,
    SkillMetadata,
    SkillOutput,
)

_log = get_logger("skills.review_changes")

_SYSTEM_PROMPT = """You are ORBIT, an expert code reviewer.
Analyze the diff provided and produce a structured Markdown review that includes:
- Summary of changes
- Risk assessment (low/medium/high)
- Key concerns
- Suggestions

Be concise and technically precise."""


class ReviewChangesSkill:
    """Analyzes changes in a repository branch using Git + LLM."""

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            id="orbit.review.changes",
            name="Review Changes",
            description="Analyzes a diff between the current state and a target branch.",
            category=SkillCategory.ANALYSIS,
            capabilities=SkillCapability(
                required_capabilities=frozenset({
                    "git.repository.read",
                    "git.diff.read",
                    "llm.complete",
                })
            ),
            version="0.1.0",
        )

    def execute(self, input_data: SkillInput, context: OrbitSkillContext) -> SkillOutput:
        """Execute the review changes skill."""
        assert isinstance(input_data, ReviewChangesInput)

        git_engine = context.resolve("git.repository.read")
        llm = context.resolve("llm.complete")

        repo = git_engine.open(input_data.repository_path)

        # Get diff between HEAD and target branch
        current_branch = git_engine.branches().current(repo)
        diff = git_engine.diff().diff_between(repo, input_data.target_branch, current_branch.name)

        prompt_parts = [
            f"# Code Review: {current_branch.name} vs {input_data.target_branch}",
            f"Files changed: {diff.stats.files_changed}",
            f"Insertions: {diff.stats.insertions}",
            f"Deletions: {diff.stats.deletions}",
            "",
            "## Changed Files",
        ]
        for f in diff.files:
            prompt_parts.append(f"- `{f.path}` ({f.status}) +{f.insertions}/-{f.deletions}")

        response = llm.complete("\n".join(prompt_parts), system=_SYSTEM_PROMPT)

        # Extract a simple risk score from the response
        risk = 0.5
        content_lower = response.content.lower()
        if "high risk" in content_lower or "critical" in content_lower:
            risk = 0.9
        elif "low risk" in content_lower:
            risk = 0.2

        return ReviewChangesOutput(
            diff_summary=response.content,
            risk_score=risk,
        )
