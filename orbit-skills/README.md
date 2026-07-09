# ORBIT Skills

High-level orchestration layer for the ORBIT platform.

## What is ORBIT Skills?

`orbit-skills` is the orchestration engine that exposes multi-engine workflows as unified, declarative capabilities (Skills). It connects the filesystem, terminal, and AI inference (via LLMs) to provide autonomous tools for consumers like Open WebUI, MCP, Claude Code, and Gemini CLI.

It dynamically resolves dependencies at runtime using a Capability Registry, meaning Skills express what they need (e.g., `git.repository.read`, `llm.complete`) without knowing how the underlying engines operate.

## Requirements

- **Python:** 3.10 or higher.
- **Package Manager:** `uv`
- **LLM Server:** OpenAI-compatible API running locally (e.g., LM Studio on `http://localhost:1234/v1`).

## Installation

```bash
uv sync
```

## First Use

```python
from orbit_skills.bootstrap import OrbitBootstrap
from orbit_skills.models import SkillRequest, RepositorySummaryInput

# Bootstrap the entire ORBIT runtime
bootstrap = OrbitBootstrap()
executor = bootstrap.bootstrap()

# Request a Repository Summary
request = SkillRequest(
    skill_id="orbit.repository.summary",
    input_data=RepositorySummaryInput(repository_path=".")
)

# Execute the workflow securely
result = executor.execute(request)
if result.success:
    print(result.output.summary_markdown)

bootstrap.shutdown()
```

## Architecture Rules

- **No Frameworks:** Pydantic is explicitly forbidden. `orbit-skills` relies exclusively on strictly-typed, standard library `dataclass(frozen=True)` models for input, output, and contexts.
- **Engine Agnostic:** The architecture must not depend on the names or existence of specific engines. It must rely strictly on `CapabilityId` matching.
- **Observability Built-in:** All execution must pass through the `SkillExecutor` to guarantee timing, logging, and event emission.
