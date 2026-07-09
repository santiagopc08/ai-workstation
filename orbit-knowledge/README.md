# ORBIT Knowledge

The structured documentation and context extraction engine for the ORBIT platform.

## What is ORBIT Knowledge?

`orbit-knowledge` parses, indexes, and summarizes local projects and their documentation. It provides AI agents with high-fidelity, context-aware information about project structure, architectural decisions, and recent changes. 

It exposes integration adapters like `GitKnowledgeService` which seamlessly merges Git repository state with underlying project documentation, acting as a context aggregator for higher-level orchestrators.

## Requirements

- **Python:** 3.10 or higher.
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
from orbit_git.integration import GitKnowledgeService

# Initialize the underlying stack
events = EventBus()
execution = ExecutionEngine()
git = GitEngine(execution, events)

# Initialize Knowledge integration
knowledge = GitKnowledgeService(git)

# Ask Knowledge for a summary of a commit's context
repo = git.open("/path/to/repo")
summary = knowledge.summarize_commit(repo, "HEAD")

print(summary)
```

## Architecture Rules

- **Zero Core Dependencies:** Like other engines, `orbit-knowledge` relies exclusively on standard Python libraries.
- **Immutable Context:** Context representations (e.g. `Document`, `Chunk`, `Project`) must be strictly modeled using `dataclasses(frozen=True)`.
- **Public API Boundary:** External consumers must only interact with Knowledge through public service interfaces, never by parsing internal structures.
