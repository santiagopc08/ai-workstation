# ORBIT Execution: Public Concepts and Process Model

## 1. Process Model

The domain model revolves around strongly typed records representing the lifecycle of an execution.

- **`ExecutionRequest`**: Represents the intent to execute. Contains the command (`list[str]`), working directory, environment overrides, and `ExecutionOptions`.
- **`ExecutionOptions`**: Modifiers for the execution (e.g., `streaming_mode`, `encoding`, `merge_stderr`).
- **`ExecutionPolicy`**: Security and bounding constraints (e.g., `max_timeout_sec`, `max_memory_mb`, `allowed_cwds`).
- **`ProcessHandle`**: An opaque reference to an accepted and validated process request before it starts.
- **`RunningProcess`**: Represents an actively executing process. Provides methods to interact (`send_stdin()`, `cancel()`) and properties for observation (`pid`, `start_time`).
- **`CompletedProcess`**: The terminal state. Contains `exit_code`, `duration_ms`, and full standard streams (if buffered).
- **`ExecutionResult`**: The final output payload wrapping a `CompletedProcess`.
- **`ExecutionError`**: Specific exception thrown when execution fails at the system level (e.g., executable not found, permissions denied).

## 2. Execution Lifecycle

1. **`initialize()`**: Bootstraps the `ExecutionEngine`, registers it with `orbit-core`, and starts internal background threads (e.g., stream pumping).
2. **`submit(request)`**: Accepts an `ExecutionRequest`, applies the `PolicyEngine` validation, and returns a `ProcessHandle`.
3. **`start(handle)`**: Actually spawns the OS process, transitioning to a `RunningProcess`.
4. **`cancel(handle, token)`**: Aborts an execution based on the rules of the cancellation token.
5. **`kill(handle)`**: Immediate hard termination.
6. **`cleanup()` / `shutdown()`**: Stops all running processes gracefully and releases OS resources.

## 3. Streaming and I/O

ORBIT Execution treats streaming as a primary concern:
- **Modes**:
  - `BUFFERED`: Streams are collected entirely in memory and returned upon completion.
  - `LINE_BY_LINE`: A callback is fired for every `\n` emitted.
  - `RAW_BINARY`: Useful for streaming non-text payloads.
- **`StreamingManager`**: Coordinates background thread pumping for `stdout` and `stderr` to avoid deadlocks. Consumers can subscribe to these streams using asynchronous iterators or callback hooks.

## 4. Cancellation Management

Cancellation must be robust and predictable.
- **`CancellationToken`**: Passed into long-running tasks. Triggering the token initiates the cancellation workflow.
- **Graceful Shutdown**: Sends `SIGTERM` (or `CTRL_C_EVENT` on Windows), allowing the process a configurable grace period to clean up.
- **Hard Kill**: Sends `SIGKILL` (or `TerminateProcess`) if the grace period expires.
- **Kill Trees**: The `CancellationManager` identifies all child processes recursively and terminates the entire tree to prevent orphans.

## 5. Policy Engine

The `PolicyEngine` is evaluated strictly *before* process creation:
- `allowed_cwds` / `blocked_cwds`: Directory sandboxing using `orbit_core.utils.paths`.
- `env_whitelist` / `env_blacklist`: Stripping sensitive environment variables (e.g., AWS keys, ORBIT internal configs) from the subprocess environment.
- `prohibited_commands`: Blocking dangerous or interactive binaries (e.g., `rm -rf`, `vim`, `nano`).
- `timeout_sec`: Enforcing strict chronological boundaries on execution.
