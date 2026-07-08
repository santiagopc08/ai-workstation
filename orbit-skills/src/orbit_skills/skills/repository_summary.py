"""Repository Summary Skill — The first fully functional ORBIT Skill.

Flow:
1. Open repository, get status.
2. Get last N commits.
3. Get recent diff.
4. Get related documentation from Knowledge.
5. Assemble a rich context prompt.
6. Send to LLM via LM Studio.
7. Return RepositorySummaryOutput.
"""

from __future__ import annotations

from orbit_core.logging import get_logger

from orbit_skills.context import OrbitSkillContext
from orbit_skills.models import (
    RepositorySummaryInput,
    RepositorySummaryOutput,
    SkillCapability,
    SkillCategory,
    SkillInput,
    SkillMetadata,
    SkillOutput,
)

_log = get_logger("skills.repository_summary")

_SYSTEM_PROMPT = """You are ORBIT, an expert repository analyst.
Analyze the repository context provided and produce a comprehensive Markdown summary that answers:
- What is this project about?
- What are its main components?
- What changed recently?
- What technologies does it use?
- What documentation is related?

Be concise, structured, and technically precise."""


class RepositorySummarySkill:
    """Generates a comprehensive repository summary using Git + Knowledge + LLM."""

    @property
    def metadata(self) -> SkillMetadata:
        return SkillMetadata(
            id="orbit.repository.summary",
            name="Repository Summary",
            description=(
                "Generates a comprehensive summary of a Git repository"
                " using Git data, Knowledge context, and LLM analysis."
            ),
            category=SkillCategory.ANALYSIS,
            capabilities=SkillCapability(
                required_capabilities=frozenset({
                    "git.repository.read",
                    "git.history.read",
                    "git.diff.read",
                    "knowledge.summary",
                    "llm.complete",
                })
            ),
            version="0.1.0",
        )

    def execute(self, input_data: SkillInput, context: OrbitSkillContext) -> SkillOutput:
        """Execute the repository summary skill."""
        assert isinstance(input_data, RepositorySummaryInput)

        git_engine = context.resolve("git.repository.read")
        knowledge_svc = context.resolve("knowledge.summary")
        llm = context.resolve("llm.complete")

        _log.info(f"Summarizing repository: {input_data.repository_path}")

        # 1. Open repository and get status
        repo = git_engine.open(input_data.repository_path)
        status = git_engine.status(repo)

        # 2. Get recent commits
        commits = git_engine.history().log(repo)[:10]

        # 3. Get recent diff (if there are at least 2 commits)
        diff_context = ""
        if len(commits) >= 2:
            diff_summary = knowledge_svc.summarize_diff(repo, commits[-1].hash, commits[0].hash)
            diff_context = diff_summary

        # 4. Get Knowledge context
        knowledge_context = ""
        try:
            repo_summary = knowledge_svc.repository_summary(repo, repo.path.split("/")[-1])
            knowledge_context = repo_summary
        except Exception:
            knowledge_context = "Knowledge context not available."

        # 5. Assemble prompt
        prompt_parts = [
            f"# Repository: {input_data.repository_path}",
            "",
            f"## Status: {status.branch}",
            f"Staged files: {len(status.staged)}",
            f"Unstaged files: {len(status.unstaged)}",
            f"Untracked files: {len(status.untracked)}",
            "",
            "## Recent Commits",
        ]
        for c in commits[:10]:
            prompt_parts.append(f"- {c.hash[:7]} ({c.author}): {c.message}")

        if diff_context:
            prompt_parts.extend(["", "## Diff Context", diff_context])

        if knowledge_context:
            prompt_parts.extend(["", "## Knowledge Context", knowledge_context])

        prompt = "\n".join(prompt_parts)

        # 6. Send to LLM
        _log.info("Sending context to LLM...")
        response = llm.complete(prompt, system=_SYSTEM_PROMPT)
        _log.info(f"LLM response received ({response.tokens_sent} sent, {response.tokens_received} received)")

        # 7. Return structured output
        return RepositorySummaryOutput(
            project_name=repo.path.split("/")[-1],
            commit_count=len(commits),
            summary_markdown=response.content,
        )
