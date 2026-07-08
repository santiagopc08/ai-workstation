# ORBIT Execution: Public API

This document defines the strict, public API contract for ORBIT Execution. It contains no OS-specific leaks, no external dependencies, and is purely built on `orbit-core`.

## 1. Core Interfaces

### `ExecutionEngine`
- **Purpose**: The main entry point for the ORBIT Execution platform.
- **Responsibilities**: Route requests to providers, enforce policies, merge configuration, manage lifecycle.
- **Methods**:
  - `execute(request: ExecutionRequest) -> ExecutionResult`
  - `execute_async(request: ExecutionRequest) -> ProcessHandle`
  - `wait(handle: ProcessHandle) -> ExecutionResult`
  - `cancel(handle: ProcessHandle, token: CancellationToken) -> None`
- **Invariants**: Must validate policy before invoking any provider.

### `ExecutionProvider`
- **Purpose**: SPI (Service Provider Interface) for execution backends (Local, SSH, Docker).
- **Responsibilities**: Spawning and managing the actual OS-level process.
- **Methods**:
  - `spawn(request: ExecutionRequest) -> RunningProcess`
  - `kill(pid: int) -> None`
- **Relationships**: Internal to `ExecutionEngine`.

## 2. Models & Records

### `ExecutionRequest`
- **Purpose**: Intent to execute.
- **Properties**: `command: list[str]`, `cwd: str | None`, `env: dict[str, str]`, `options: ExecutionOptions`, `policy: ExecutionPolicy | None`.
- **Invariants**: `command` must be a list (shell injection prevention).

### `ExecutionOptions`
- **Purpose**: Modifiers for how the execution behaves.
- **Properties**: `merge_stderr: bool`, `encoding: str` (default `utf-8`), `publish_streams: bool`.

### `ExecutionPolicy`
- **Purpose**: Security and bounding constraints.
- **Properties**: `timeout_sec: int`, `max_memory_mb: int`, `allowed_cwds: list[str]`, `env_whitelist: list[str]`.
- **Inheritance Resolution**: Evaluated at runtime in the order: **Request > Engine > Global**.

### `ProcessHandle`
- **Purpose**: Opaque reference to an active or pending async execution.
- **Properties**: `id: str`, `request: ExecutionRequest`.

### `RunningProcess`
- **Purpose**: Live interface to a spawned process.
- **Properties**: `handle: ProcessHandle`, `pid: int`, `start_time: float`.
- **Methods**: `send_stdin(data: bytes) -> None`

### `CompletedProcess`
- **Purpose**: Terminal state data.
- **Properties**: `handle: ProcessHandle`, `exit_code: int`, `stdout: bytes`, `stderr: bytes`, `duration_ms: int`.

### `ExecutionResult`
- **Purpose**: Final payload returned to the caller.
- **Properties**: `process: CompletedProcess`.

### `CancellationToken`
- **Purpose**: Signal payload for cooperative or aggressive cancellation.
- **Properties**: `reason: str`, `force_kill: bool` (whether to skip SIGTERM and go to SIGKILL).

## 3. Streaming Events (EventBus)

Streaming uses the `orbit-core` EventBus. No callbacks are used in the API.

### `StreamEvent` (Base)
- **Properties**: `handle: ProcessHandle`, `timestamp: float`.

**Implementations**:
- `StdoutChunk(chunk: bytes)`
- `StderrChunk(chunk: bytes)`
- `ProcessStarted(pid: int)`
- `ProcessFinished(exit_code: int)`
- `ProcessFailed(error: str)`
- `TimeoutReached()`
- `ProcessCancelled(reason: str)`

## 4. Exceptions

- `ExecutionError`: Base class for execution failures.
- `PolicyViolationError`: Thrown before spawning if the request breaches `ExecutionPolicy`.
- `TimeoutError`: Thrown if `timeout_sec` is breached.

## 5. Capabilities

The engine must register granular capabilities via the `orbit-core` Registry:
- `exec.local`: Can execute on the host.
- `exec.process`: Can manage process lifecycles.
- `exec.streaming`: Supports EventBus streaming.
- `exec.interactive`: Supports `send_stdin`.
- `exec.binary`: Supports raw byte streaming.
