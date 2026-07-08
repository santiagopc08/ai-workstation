# Architecture Decision Record (ADR) 015: ORBIT Skills

## Status
Draft

## Context
ORBIT is composed of several powerful engines (`orbit-git`, `orbit-knowledge`, `orbit-execution`). As ORBIT matures, it is being integrated with multiple external consumers (e.g., Open WebUI, MCP, Claude Code, Gemini CLI, Codex). 

Currently, to perform high-level tasks (e.g., "Review Changes" or "Explain Commit"), consumers must interact directly with the lower-level public APIs of multiple engines and stitch the logic together themselves. This approach introduces several issues:
1. **Coupling**: External consumers become tightly coupled to the specifics of ORBIT's internal engines.
2. **Duplication**: The orchestration logic (e.g., fetching a Git diff and passing it to the Knowledge engine) is duplicated across different agent integrations.
3. **Security and Sandboxing**: Direct access to raw engines like `orbit-execution` bypasses potential higher-level validations or intent checks.
4. **Observability**: Tracking what an agent is "trying to do" is difficult when the telemetry is scattered across raw API calls to `orbit-git` or `orbit-execution`.

## Decision
We will introduce a new architectural layer: **ORBIT Skills**.

A "Skill" represents a high-level, declarative capability constructed by combining one or more ORBIT engines. All external agents and clients will interact **exclusively** with the ORBIT Skills layer rather than calling engines directly.

### Core Principles
1. **Abstraction**: Skills encapsulate multi-engine workflows. Consumers execute the Skill; they do not orchestrate the engines.
2. **Generic Capability Resolution**: Skills do not depend on hardcoded engines (e.g., `orbit-git`). Instead, they declare a set of required `CapabilityId`s (like `git.history.read`), and the `SkillContext` resolves these dependencies dynamically.
3. **Registration & Validation**: All Skills must be registered in a central `SkillRegistry` and undergo strict validation before execution.
4. **Strongly Typed I/O**: Every Skill utilizes strictly typed standard library models (e.g., `dataclasses`) for `SkillInput` and `SkillOutput` (e.g., `RepositorySummaryInput`), ensuring no generic dictionaries (`Dict`, `Any`). This avoids heavy external dependencies like Pydantic, while allowing separate optional adapters (e.g., `orbit-skills-jsonschema`) to generate JSON Schemas.
5. **Observability**: Execution flows through a unified `SkillExecutor` and a DAG-based `SkillPipeline`, which automatically instrument the operation with OrbitLogger, Metrics, and EventBus emissions.

## Consequences
### Positive
- **Simpler Integrations**: External systems (like MCP or Open WebUI) only need to discover and invoke Skills.
- **Centralized Security**: Validations can occur at the boundary of the Skill before reaching the ExecutionEngine.
- **Enhanced Telemetry**: We gain clear insights into high-level intent (e.g., "The user ran `SearchProject`" instead of "The user ran 15 grep commands").
- **Reusability**: High-level workflows are coded once as Skills and shared across all clients.

### Negative
- **Increased Overhead**: Adds a layer of indirection between the consumer and the raw engine.
- **Development Friction**: Creating a new capability requires defining a formal Skill rather than just writing a quick script on the client side.
