# ORBIT Execution: Architectural Decision Records (ADRs)

## ADR-001: Separation of Execution from Orchestration
**Context**: Various ORBIT tools need to run OS commands.
**Decision**: Create a dedicated, standalone `orbit-execution` engine rather than letting each tool call `subprocess`.
**Rationale**: Centralizing execution provides a single choke point for security policies, cross-platform normalization, timeout enforcement, stream management, and telemetry generation.
**Consequences**: Increases the initial architectural complexity but ensures deterministic and safe command execution platform-wide.

## ADR-002: Rejection of Asyncio for Core Engine
**Context**: Subprocess management often involves asynchronous stream reading (non-blocking I/O).
**Decision**: Use synchronous threading (`threading.Thread`, `queue.Queue`) instead of Python's `asyncio`.
**Rationale**: `orbit-core` explicitly rejects `asyncio` for the platform baseline to prevent "colored functions" (sync vs async contagion). Threaded stream pumping is highly stable for subprocess I/O in standard Python and keeps the API fully synchronous.
**Consequences**: The Streaming Manager must carefully handle thread lifecycles and daemon flags to prevent blocking Python shutdown.

## ADR-003: Subprocess Policy Engine Validation Before Spawning
**Context**: Executing untrusted or misconfigured commands can compromise the host OS.
**Decision**: Enforce the `PolicyEngine` (CWD validation, environment stripping, command whitelists) synchronously *before* calling the OS process spawner.
**Rationale**: Fails fast. Eliminates the risk of starting a malicious process and attempting to kill it later.
**Consequences**: All engines must pre-declare their required environment variables and working directories, which increases configuration strictness.

## ADR-004: Execution Provider Abstraction
**Context**: Currently, commands run locally on the host. In the future, commands may need to run over SSH or inside Docker.
**Decision**: Introduce the `ExecutionProvider` Protocol. `ExecutionEngine` delegates spawning to the active provider (defaulting to `LocalExecutionProvider`).
**Rationale**: OCP (Open-Closed Principle). We can add `SSHExecutionProvider` later without changing `ExecutionEngine` or modifying downstream callers like ORBIT Git.
**Consequences**: `ExecutionProvider` must define a universal contract for process creation and cancellation that maps cleanly to SSH channels or Docker exec sessions as well as local subprocesses.

## ADR-005: Explicit CancellationToken vs Process Timeout
**Context**: Processes need to be cancelled by users or by timeout limits.
**Decision**: Implement an explicit `CancellationToken` pattern instead of relying purely on fixed timeouts.
**Rationale**: A `CancellationToken` allows cooperative cancellation initiated by external events (e.g., a user pressing a cancel button in Open WebUI), not just a chronological timeout. Timeouts are implemented by triggering the token when a timer expires.
**Consequences**: Consumers must retain the `ProcessHandle` and its token to initiate cancellation externally.
