#!/usr/bin/env python3
"""ORBIT Example — Review Changes.

Usage:
    uv run examples/review_changes.py [repository_path] [target_branch]

Defaults to the current directory and 'main' branch.
"""

from __future__ import annotations

import sys

from orbit_skills.bootstrap import OrbitBootstrap
from orbit_skills.models import ReviewChangesInput, SkillRequest


def main() -> None:
    repo_path = sys.argv[1] if len(sys.argv) > 1 else "."
    target_branch = sys.argv[2] if len(sys.argv) > 2 else "main"

    print(f"🔍 ORBIT — Review Changes")
    print(f"📂 Repository: {repo_path}")
    print(f"🌿 Target Branch: {target_branch}")
    print("─" * 60)

    # Bootstrap the ORBIT runtime
    bootstrap = OrbitBootstrap()
    executor = bootstrap.bootstrap()

    # Formulate the request
    request = SkillRequest(
        skill_id="orbit.review.changes",
        input_data=ReviewChangesInput(repository_path=repo_path, target_branch=target_branch),
    )

    # Execute the workflow securely
    result = executor.execute(request)

    if result.success and result.output:
        from orbit_skills.models import ReviewChangesOutput
        assert isinstance(result.output, ReviewChangesOutput)
        
        print(f"\n⚠️  Risk Score: {result.output.risk_score * 100:.0f}%")
        print(f"⏱️  Duration: {result.duration_ms}ms")
        print("─" * 60)
        print(result.output.diff_summary)
    else:
        print(f"\n❌ Skill failed: {result.error}")

    bootstrap.shutdown()

if __name__ == "__main__":
    main()
