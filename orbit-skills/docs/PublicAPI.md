# ORBIT Skills Public API

This document describes the primary models and interfaces for the ORBIT Skills layer.

## Models

### `SkillId`
A unique string identifier for a skill. By convention, uses dot notation representing the domain (e.g., `git.repository.summary`).

```python
SkillId = str
```

### `SkillCategory`
An enumeration of broad categories that a Skill falls under, used for discovery and filtering.

```python
from enum import Enum

class SkillCategory(Enum):
    ANALYSIS = "analysis"
    MODIFICATION = "modification"
    SEARCH = "search"
    AUTOMATION = "automation"
```

### `CapabilityId`
A unique string identifier representing a generic engine capability. By convention, uses dot notation representing the domain (e.g., `git.history.read`, `knowledge.search`, `execution.process`).

```python
CapabilityId = str
```

### `SkillCapability`
Represents the set of required privileges and generic engine access needed by the skill.

```python
from dataclasses import dataclass
from typing import FrozenSet

@dataclass(frozen=True)
class SkillCapability:
    required_capabilities: FrozenSet[CapabilityId]
```

### `SkillMetadata`
Metadata definition associated with every Skill.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SkillMetadata:
    id: SkillId
    name: str
    description: str
    category: SkillCategory
    capabilities: SkillCapability
    version: str
```

### `SkillInput` & `SkillOutput`
Base classes for strictly typed payload data. These are implemented as immutable standard library dataclasses. No generic `Dict` or `Any` types are allowed for the base payload. A separate adapter (`orbit-skills-jsonschema`) will handle translating these into JSON Schemas.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class SkillInput:
    """Base class for all skill inputs."""
    pass

@dataclass(frozen=True)
class SkillOutput:
    """Base class for all skill outputs."""
    pass

# --- Concrete Examples ---

@dataclass(frozen=True)
class RepositorySummaryInput(SkillInput):
    repository_path: str
    include_history: bool = True

@dataclass(frozen=True)
class RepositorySummaryOutput(SkillOutput):
    project_name: str
    commit_count: int
    summary_markdown: str

@dataclass(frozen=True)
class ReviewChangesInput(SkillInput):
    repository_path: str
    target_branch: str
    
@dataclass(frozen=True)
class ReviewChangesOutput(SkillOutput):
    diff_summary: str
    risk_score: float

@dataclass(frozen=True)
class ExplainCommitInput(SkillInput):
    repository_path: str
    commit_hash: str
    
@dataclass(frozen=True)
class ExplainCommitOutput(SkillOutput):
    explanation: str
    affected_files: list[str]
```

### `SkillError`
Standardized error representation.

```python
@dataclass
class SkillError(Exception):
    skill_id: SkillId
    message: str
    code: str
    details: dict[str, str]
```

### `SkillRequest`
The envelope structure representing a request from a consumer.

```python
@dataclass(frozen=True)
class SkillRequest:
    skill_id: SkillId
    input_data: SkillInput
    idempotency_key: str | None = None
    timeout_ms: int | None = None
```

### `SkillResult`
The envelope structure containing the final execution output.

```python
@dataclass(frozen=True)
class SkillResult:
    skill_id: SkillId
    success: bool
    output: SkillOutput | None = None
    error: SkillError | None = None
    duration_ms: int = 0
```

---

## Interfaces

### `SkillContext`
The runtime environment passed to a Skill.

```python
from typing import Protocol, TypeVar, Any
from orbit_core.events import EventBus

T = TypeVar('T')

class SkillContext(Protocol):
    def resolve(self, capability: CapabilityId) -> Any:
        """Dynamically resolves a requested capability ID to the concrete engine interface."""
        ...
        
    @property
    def events(self) -> EventBus: ...
```

### `ISkill`
The core interface that every capability must implement.

```python
class ISkill(Protocol):
    @property
    def metadata(self) -> SkillMetadata: ...

    def execute(self, input_data: SkillInput, context: SkillContext) -> SkillOutput:
        """Executes the skill business logic."""
        ...
```

### `ISkillRegistry`
The central registry interface.

```python
class ISkillRegistry(Protocol):
    def register(self, skill: ISkill) -> None: ...
    def get(self, skill_id: SkillId) -> ISkill: ...
    def list_skills(self, category: SkillCategory | None = None) -> list[SkillMetadata]: ...
```

### `ISkillExecutor`
The entry point for consumers to invoke a skill securely.

```python
class ISkillExecutor(Protocol):
    def execute(self, request: SkillRequest) -> SkillResult:
        """Validates the request, provisions the context, and executes the skill."""
        ...
```
