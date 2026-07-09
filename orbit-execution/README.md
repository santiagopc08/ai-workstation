# ORBIT Execution

The secure, observable, and isolated process execution engine for the ORBIT platform.

## What is ORBIT Execution?

`orbit-execution` acts as the sole gateway for spawning external processes in the ORBIT ecosystem. It intercepts, validates, and manages process execution, ensuring that no malicious or runaway commands are executed by AI agents.

It provides a safe wrapper around standard subprocess APIs, introducing features like:
- **Timeouts:** Automatic termination of runaway processes.
- **Resource Limits:** Restricting execution scope.
- **Observability:** Emitting structured events (`ProcessStarted`, `ProcessCompleted`, `ProcessFailed`) to the `orbit-core` EventBus.

## Requirements

- **Python:** 3.10 or higher.
- **Package Manager:** `uv`

## Installation

```bash
uv sync
```

## First Use

```python
from orbit_execution import ExecutionEngine
from orbit_execution.models import Command

# Initialize the engine
engine = ExecutionEngine()

# Define and run a command safely
cmd = Command(
    executable="echo",
    args=["Hello, ORBIT!"],
    timeout_seconds=5
)

result = engine.run(cmd)
print(f"Status: {result.exit_code}")
print(f"Output: {result.stdout}")
```

## Architecture Rules

- **Zero Dependencies:** `orbit-execution` must absolutely NEVER depend on external third-party libraries. It uses the Python standard library `subprocess` internally.
- **Centralized Execution:** No other engine in the ORBIT platform is allowed to spawn subprocesses directly. They must all route requests through `orbit-execution`.
