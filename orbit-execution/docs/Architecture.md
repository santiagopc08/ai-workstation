# ORBIT Execution Architecture

## 1. Context and Vision
ORBIT Execution is the foundational engine responsible for executing any operating system process securely, observably, and independently. It acts as the exclusive gateway for all subprocess invocations across the ORBIT platform. Engines like ORBIT Git, ORBIT Docker, and ORBIT Memory must never invoke `subprocess` directly; they must route all executions through ORBIT Execution.

## 2. Responsibilities
### What Execution DOES:
- Spawns and manages OS-level processes.
- Enforces execution policies (timeout, max memory, allowed working directories, environment filtering).
- Streams standard streams (`stdout`, `stderr`, `stdin`) as text or binary.
- Manages process lifecycle (cancellation, tree killing, graceful shutdown).
- Exposes execution events, metrics, and health to the ORBIT Event Bus and Metrics Collector.

### What Execution does NOT do:
- **No business logic:** It does not know what a "git commit" or a "docker build" is.
- **No prompt management:** It does not integrate with LLMs or manage intelligent agents.
- **No high-level orchestration:** Workflows and DAGs belong in ORBIT Orchestrator.
- **No external state persistence:** While it generates logs and events, historical persistence of execution runs is the responsibility of ORBIT Memory.

## 3. Integration with ORBIT Core
ORBIT Execution is built strictly on top of `orbit-core` and the Python Standard Library.
- **Registry & Capabilities**: The engine registers itself and its capabilities (e.g., `Capability(id="exec.local", ...)`).
- **DI Container**: Resolves dependencies such as `Logger`, `EventBus`, and `MetricsCollector`.
- **Health**: Registers a `HealthCheck` to report whether the execution environment (e.g., shell availability, permissions) is degraded.
- **Events**: Publishes lifecycle events (`ProcessStarted`, `ProcessCompleted`, `ProcessFailed`) through `orbit_core.events.bus`.
- **Config**: Consumes configurations like default timeouts and restricted paths via `SettingsManager`.
- **Exceptions**: Emits typed exceptions extending `OrbitError` (e.g., `ExecutionError`, `PolicyViolationError`).
- **Protocols**: Implements the `Engine` and `TerminalProvider` (if applicable) interfaces.

## 4. Security Architecture
Executing arbitrary processes is inherently dangerous. ORBIT Execution mitigates risks through:
- **Path Traversal & CWD Constraints**: Uses `orbit_core.utils.paths.safe_join` and `is_inside` to strictly bound working directories to allowed scopes.
- **Environment Isolation**: `EnvironmentResolver` sanitizes environment variables, enforcing explicitly allowed keys and dropping restricted ones (e.g., stripping local API keys unless explicitly whitelisted).
- **Process Trees & Fork Bombs**: `ProcessManager` tracks child processes (process groups on Linux/macOS, Job Objects on Windows) to guarantee complete cleanup on cancellation, preventing orphan and zombie processes.
- **Shell Injection**: Disallows `shell=True` by default. Requires explicit policy bypass with pre-parsed argument lists (`list[str]`) for commands.

## 5. Extensibility
The architecture relies on the `ExecutionProvider` interface. The initial implementation is `LocalExecutionProvider` (using standard `subprocess`), but the design inherently supports future injections of:
- `SSHExecutionProvider` (for remote execution via paramiko/asyncssh abstractions).
- `DockerExecutionProvider` (executing inside containers).
- `WslExecutionProvider` (bridging Windows hosts to WSL environments).
These providers implement the same `ExecutionProvider` protocol, allowing ORBIT tools to execute commands seamlessly across boundaries without modifying the public API.

## 6. Architectural Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| **Zombie Processes** | Implement strict cross-platform process tree termination (SIGTERM -> SIGKILL cascade, Job Objects on Windows). |
| **Stream Deadlocks** | Use separate threads for non-blocking I/O pumping of `stdout` and `stderr` to prevent OS pipe buffers from filling and hanging the process. |
| **Resource Exhaustion** | Enforce strict bounded policies on memory consumption (via OS limits like `ulimit` or `cgroups` if available) and strict timeout cancellations. |
