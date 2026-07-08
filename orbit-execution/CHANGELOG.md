# Changelog

## [0.1.0] - 2026-07-07

### Added
- **Sprint 1 Release:** Basic local process execution functionality.
- `ExecutionEngine` implementation supporting `execute()` and `execute_async()`.
- `LocalExecutionProvider` using `subprocess` under the hood.
- Strict immutable datatypes: `ExecutionRequest`, `ExecutionResult`, `CompletedProcess`, etc.
- Support for `CancellationToken` (basic `SIGTERM` / `SIGKILL` implementations).
- Robust handling of `timeout_sec` in `ExecutionPolicy`.
- Output buffering and error merging functionality via `ExecutionOptions`.

### Fixed (Audit)
- Fixed an issue where cancelled or failed processes incorrectly mapped to `ProcessState.EXITED`. They now correctly map to `CANCELLED` and `FAILED` respectively.
- Ensured timeouts correctly purge tracked cancellation states to prevent memory leaks in the engine.

## [0.2.0] - 2026-07-07

### Added
- **Sprint 2 Release:** Real-time Process Streaming.
- Added synchronous lifecycle events: `ProcessStarted`, `ProcessFinished`, `ProcessFailed`, `ProcessCancelled`, `TimeoutReached`.
- Added chunked standard stream events: `StdoutChunk`, `StderrChunk`.
- Integrated `ExecutionEngine` with `orbit_core.events.bus.EventBus`.
- Added daemon thread buffering to continually ingest output regardless of consumer, eliminating deadlocks caused by full pipes.

## [0.3.0] - 2026-07-07

### Added
- **Sprint 3 Release:** Execution Policy Engine.
- `PolicyManager`, `PolicyResolver`, and `PolicyValidator` to securely control parameters before process spawning.
- Support for `allowed_cwds`, `blocked_cwds`, `env_whitelist`, `env_blacklist`, `command_whitelist`, `command_blacklist`, `allow_shell`, and `interactive_allowed`.
- Hierarchical policy inheritance (Request > Engine > Global) via fallback merging.
- Fails fast by triggering `PolicyViolationError` without touching standard library internals.

## [0.4.0] - 2026-07-07

### Added
- **Sprint 4 Release:** Execution Observability Layer.
- `ExecutionTracer` which consumes real-time `EventBus` payloads to build accurate execution traces (`ExecutionMetrics`).
- `InternalMetricsCollector` to maintain aggregate percentiles and cumulative counters (successful, failed, timeout, violations).
- Structured JSON-compatible logging strictly compatible with `orbit-core`'s `OrbitLogger`.
- Added transparent `execution_id` injection across traces, metrics, and structured log records.
- Standardized `HealthReporter` implementation adhering seamlessly to `orbit-core` `HealthCheck` bounds.

## [0.5.0] - 2026-07-07

### Added
- **Sprint 5 Release:** OS-level Sandboxing Layer.
- `SandboxManager` and `SandboxValidator` to actively secure executions before dispatch.
- Defeats Path Traversal vectors explicitly using `os.path.realpath` logic.
- Blocks symlink escaping bounds during CWD validation.
- Validates executable presence (`shutil.which`) and real system permissions (`os.access`) gracefully.
- Explicit blocking of terminal shells (e.g., `bash`, `sh`) bypassing constraints via symlinking.
- New `SandboxViolationError` cleanly decoupling logical policy errors from physical system infractions.
