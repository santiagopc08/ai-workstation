# ORBIT Git

The safe, observable, and isolated Git engine for the ORBIT ecosystem.

## What is ORBIT Git?

`orbit-git` provides a high-level Python API for interacting with Git repositories. It implements the Git operations needed by the ORBIT platform without directly invoking `subprocess` or relying on external C-based Git libraries like `pygit2`.

Instead, `orbit-git` uses `orbit-execution` to spawn sandboxed processes. All Git output is parsed synchronously into fully typed standard library `dataclass` structures (e.g., `Branch`, `Commit`, `Status`, `Diff`).

## Requirements

- **Python:** 3.10 or higher.
- **Git:** 2.30 or higher (must be on system PATH).
- **Package Manager:** `uv`

## Installation

```bash
uv sync
```

## First Use

```python
from orbit_core.events import EventBus
from orbit_execution import ExecutionEngine
from orbit_git import GitEngine

# Initialize underlying engines
events = EventBus()
execution = ExecutionEngine()

# Initialize GitEngine
git = GitEngine(execution, events)

# Open a local repository and get its status
repo = git.open("/path/to/repo")
status = git.status(repo)

print(f"Current branch: {status.branch}")
print(f"Modified files: {len(status.unstaged)}")
```

## Architecture Rules

- **No Subprocess:** `orbit-git` must NEVER call `subprocess`, `os.system`, or similar APIs directly. All execution must go through the injected `ExecutionEngine`.
- **No Third-Party Git Bindings:** Do not use `GitPython` or `pygit2`. We execute the native Git binary.
- **Strict Parsing:** Do not use fragile regex where Git provides structured output formats (e.g., use `git diff --numstat` instead of parsing standard patches).
