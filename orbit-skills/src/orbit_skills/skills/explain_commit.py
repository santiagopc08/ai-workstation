"""Explain Commit Skill — Explains a specific commit."""

from __future__ import annotations

from orbit_core.logging import get_logger

from orbit_skills.context import OrbitSkillContext
from orbit_skills.models import (
    ExplainCommitInput,
    ExplainCommitOutput,
    SkillCapability,
    SkillCategory,
    SkillInput,
    SkillMetadata,
    SkillOutput,
)

_log = get_logger("skills.explain_commit")

_SYSTEM_PROMPT = """You are ORBIT, an expert at explaining Git commits.
Given a commit's details and changed files, explain:
- What this commit does
- Why these changes were made
- What files are affected

Be concise and technically precise."""


class ExplainCommitSkill:
    """Explains a specific commit using Git + LLM."""

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            id="orbit.explain.commit",
            name="Explain Commit",
            description="Explains a specific Git commit using LLM analysis.",
            category=SkillCategory.ANALYSIS,
            capabilities=SkillCapability(
                required_capabilities=frozenset({
                    "git.repository.read",
                    "git.history.read",
                    "llm.complete",
                })
            ),
            version="0.1.0",
        )

    def execute(self, input_data: SkillInput, context: OrbitSkillContext) -> SkillOutput:
        """Execute the explain commit skill."""
        assert isinstance(input_data, ExplainCommitInput)

        git_engine = context.resolve("git.repository.read")
        llm = context.resolve("llm.complete")

        repo = git_engine.open(input_data.repository_path)
        commit, diff = git_engine.history().show(repo, input_data.commit_hash)

        prompt_parts = [
            f"# Commit: {commit.hash}",
            f"Author: {commit.author}",
            f"Date: {commit.date}",
            f"Message: {commit.message}",
            "",
            "## Changed Files",
        ]
        for f in diff.files:
            prompt_parts.append(f"- `{f.path}` ({f.status}) +{f.insertions}/-{f.deletions}")

        response = llm.complete("\n".join(prompt_parts), system=_SYSTEM_PROMPT)

        return ExplainCommitOutput(
            explanation=response.content,
            affected_files=tuple(f.path for f in diff.files),
        )
