#!/usr/bin/env python3
"""ORBIT Demo — Repository Summary.

Usage:
    python demo_repository_summary.py [repository_path]

Defaults to the current directory if no path is provided.
"""

from __future__ import annotations

import sys

from orbit_skills.bootstrap import OrbitBootstrap
from orbit_skills.llm import LLMConfig
from orbit_skills.models import RepositorySummaryInput, SkillRequest


def main() -> None:
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."

    print(f"🔭 ORBIT — Repository Summary")
    print(f"📂 Repository: {repo_path}")
    print("─" * 60)

    # Bootstrap with default LM Studio config
    config = LLMConfig(
        endpoint="http://localhost:1234/v1",
        model="default",
        temperature=0.3,
        max_tokens=2048,
    )
    bootstrap = OrbitBootstrap(llm_config=config)
    executor = bootstrap.bootstrap()

    # Execute the Repository Summary skill
    request = SkillRequest(
        skill_id="orbit.repository.summary",
        input_data=RepositorySummaryInput(repository_path=repo_path),
    )

    result = executor.execute(request)

    if result.success and result.output:
        from orbit_skills.models import RepositorySummaryOutput

        assert isinstance(result.output, RepositorySummaryOutput)
        print(f"\n📊 Project: {result.output.project_name}")
        print(f"📝 Commits analyzed: {result.output.commit_count}")
        print(f"⏱️  Duration: {result.duration_ms}ms")
        print("─" * 60)
        print(result.output.summary_markdown)
    else:
        print(f"\n❌ Skill failed: {result.error}")

    bootstrap.shutdown()


if __name__ == "__main__":
    main()
