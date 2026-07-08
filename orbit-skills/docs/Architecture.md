# ORBIT Skills Architecture

## Overview
ORBIT Skills is the high-level orchestration layer of the ORBIT platform. It encapsulates multiple foundational engines (`orbit-git`, `orbit-knowledge`, `orbit-execution`) into unified, declarative capabilities (Skills) exposed to external consumers.

## Core Concepts

### `Skill`
A `Skill` is the core abstraction representing a discrete, high-level capability. 
- It encapsulates the business logic required to satisfy a `SkillRequest`.
- It interacts **strictly** with the public APIs of ORBIT engines.
- Skills must be stateless; all contextual execution data is passed via `SkillContext`.

### `SkillMetadata`
Each `Skill` defines static metadata:
- **`SkillId`**: Unique identifier (e.g., `git.repository.summary`).
- **`SkillCategory`**: Broad classification (e.g., `ANALYSIS`, `MODIFICATION`, `SEARCH`).
- **`SkillCapability`**: Defines a set of generic `CapabilityId`s required by the skill (e.g., `git.history.read`, `knowledge.search`). This decouples the skill from hardcoded engine names.

### `SkillRegistry`
The central repository for all available Skills. 
- External consumers interrogate the `SkillRegistry` to discover what actions they can perform.
- Handles registration, dependency validation, and collision resolution for overlapping `SkillId`s.

### `SkillRequest` & `SkillResult`
- **`SkillRequest`**: A strictly typed immutable structure encapsulating input parameters (`SkillInput`), origin identifiers, and execution preferences (timeout, idempotency keys). `SkillInput` instances are implemented as immutable standard library dataclasses (e.g., `RepositorySummaryInput`), ensuring straightforward generation of JSON Schemas via adapters.
- **`SkillResult`**: A strictly typed output envelope encapsulating the payload (`SkillOutput` dataclass, e.g., `RepositorySummaryOutput`), execution duration, and potential `SkillError` structures if execution failed.

### `SkillContext`
The runtime environment provisioned for a specific execution. It provides:
- A generic capability resolution mechanism (e.g., `resolve(CapabilityId)`) that fetches the appropriate capability interface dynamically without hardcoding engine references (no `context.git` or `context.execution`).
- OrbitLogger for structured logging.
- Telemetry handles.
- Dependency injection hooks.

### `SkillExecutor` & `SkillPipeline`
- **`SkillExecutor`**: The runtime boundary responsible for executing a single skill. It acts as the gateway handling context provisioning, timeout enforcement, and isolation.
- **`SkillPipeline`**: A Directed Acyclic Graph (DAG) composition engine that orchestrates multiple skills. Nodes represent individual Skills and edges represent data or temporal dependencies. It handles dependency resolution, pre-flight validation, and lays the groundwork for future parallel execution of independent skills.

### `SkillValidator`
A pre-execution interceptor that verifies:
- Is the consumer authorized?
- Are the requested parameters (`SkillInput`) structurally sound?
- Do the requested engines currently report healthy statuses?

## Integration & Extensibility

### Engine Integration
Skills integrate with ORBIT engines (Execution, Git, Knowledge) exclusively via their public APIs. Access to internals (`_private_methods`) is strictly forbidden and structurally isolated. 

### Extensibility Models
- **Synchronous Skills**: Return results immediately. Best for fast operations like `SearchProject`.
- **Long-running Skills**: Support for asynchronous execution, yielding a job token or relying on EventBus streams. Best for `PrepareRelease`.
- **Composite Skills**: Skills that do not implement logic directly but orchestrate other Skills via `SkillPipeline`.
- **Parameterized Skills**: Skills that accept strongly typed JSON schemas as input, ideal for dynamic LLM tool mapping.

## Observability
Execution through the `SkillExecutor` guarantees built-in observability:
- **OrbitLogger**: Structured, execution-tagged logging (no `print()` statements).
- **Metrics**: Standardized counters and histograms (executions, latency, error rates).
- **EventBus**: Emits events (e.g., `SkillExecutionStarted`, `SkillExecutionCompleted`) allowing external systems to react to state changes asynchronously.
- **Health**: Exposes composite health checks covering both the registered skills and their dependent engines.
