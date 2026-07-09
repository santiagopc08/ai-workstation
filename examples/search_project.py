#!/usr/bin/env python3
"""ORBIT Example — Search Project.

Usage:
    uv run examples/search_project.py [repository_path] [query]

Defaults to the current directory if no path is provided.
"""

from __future__ import annotations

import sys

from orbit_skills.bootstrap import OrbitBootstrap
from orbit_skills.models import SearchProjectInput, SkillRequest


def main() -> None:
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    query = sys.argv[2] if len(sys.argv) > 2 else "architecture"

    print(f"🔎 ORBIT — Search Project")
    print(f"📂 Repository: {repo_path}")
    print(f"❓ Query: '{query}'")
    print("─" * 60)

    # Bootstrap the ORBIT runtime
    bootstrap = OrbitBootstrap()
    executor = bootstrap.bootstrap()

    # Formulate the request
    request = SkillRequest(
        skill_id="orbit.search.project",
        input_data=SearchProjectInput(project_path=repo_path, query=query),
    )

    # Execute the workflow securely
    result = executor.execute(request)

    if result.success and result.output:
        from orbit_skills.models import SearchProjectOutput
        assert isinstance(result.output, SearchProjectOutput)
        
        print(f"\n📑 Results found: {result.output.result_count}")
        print(f"⏱️  Duration: {result.duration_ms}ms")
        print("─" * 60)
        print(result.output.results_markdown)
    else:
        print(f"\n❌ Skill failed: {result.error}")

    bootstrap.shutdown()

if __name__ == "__main__":
    main()
