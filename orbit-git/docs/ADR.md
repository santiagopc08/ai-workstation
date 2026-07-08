# ORBIT Git: Architectural Decision Records (ADRs)

## ADR-001: No External Git Libraries

**Context**: Python has mature Git libraries (GitPython, pygit2) that provide Pythonic abstractions over Git operations.

**Decision**: Do not use GitPython, pygit2, or any external Git library. All Git operations are executed via the `git` CLI through `orbit-execution`.

**Rationale**:
- GitPython internally calls `subprocess` and adds a large, complex dependency surface that is difficult to audit for security.
- pygit2 requires `libgit2` native binaries, creating cross-platform packaging complexity.
- Routing all commands through `orbit-execution` gives ORBIT Git automatic access to policy enforcement, sandboxing, streaming, observability, and future execution backends (SSH, Docker) without any additional work.
- The `git` CLI is the canonical, best-tested, and most portable interface to Git.

**Consequences**: ORBIT Git must parse Git CLI output. This is mitigated by using `--porcelain`, `--format`, and machine-readable flags wherever possible.

---

## ADR-002: GitCommandRunner as Single Execution Gateway

**Context**: Multiple manager classes (BranchManager, CommitManager, etc.) all need to execute Git commands.

**Decision**: Create a single internal `GitCommandRunner` class that wraps `ExecutionEngine`. All managers receive a reference to the runner; none import or reference `ExecutionEngine` directly.

**Rationale**:
- Single point of configuration for repository-scoped `cwd`, `env`, and `ExecutionPolicy`.
- Single point of error translation (exit code → typed exception).
- Simplifies testing: mock the runner, not the execution engine.
- Enforces the invariant that every Git command passes through policy validation and sandboxing.

**Consequences**: The runner becomes a critical internal dependency. Its API must be minimal and stable.

---

## ADR-003: Manager-per-Domain Decomposition

**Context**: Git has a vast surface area (branches, commits, remotes, stashes, worktrees, submodules, config).

**Decision**: Decompose into dedicated manager classes per domain rather than a monolithic `GitEngine` with hundreds of methods.

**Rationale**:
- Each manager is independently testable.
- The `GitEngine` facade delegates to managers, keeping its own surface thin and navigable.
- Follows the same pattern as orbit-execution's internal decomposition (PolicyManager, SandboxManager, etc.).

**Consequences**: `GitEngine` must coordinate manager instantiation and lifecycle. Users interact with the engine; they do not instantiate managers directly.

---

## ADR-004: Immutable Models with Frozen Dataclasses

**Context**: Git operations return rich data structures (repository metadata, branch lists, commit details, diffs).

**Decision**: All public models (`Repository`, `Branch`, `Commit`, `Tag`, `Remote`, `Diff`, `Status`, `Stash`, `Worktree`) use frozen dataclasses with slots.

**Rationale**:
- Consistent with `orbit-core` and `orbit-execution` model conventions.
- Immutability prevents accidental mutation of returned data.
- Slots reduce memory footprint for large result sets (e.g., log with thousands of commits).

**Consequences**: Any transformation of models requires creating new instances. This is intentional — Git data is inherently snapshot-based.

---

## ADR-005: Repository-Scoped Operations

**Context**: Every Git command operates within the context of a specific repository on disk.

**Decision**: `GitEngine.open(path)` returns a `Repository` handle. All subsequent operations require a `Repository` reference. There are no "global" Git operations.

**Rationale**:
- Explicitly binds operations to a validated, sandboxed repository root.
- Prevents accidental cross-repository operations.
- `GitValidator` runs once at `open()` time, not on every command.
- The `Repository` carries the resolved real path, eliminating repeated symlink resolution.

**Consequences**: Users must `open()` a repository before performing any operation. This is a deliberate design choice, not friction.

---

## ADR-006: Events for Observable Git Lifecycle

**Context**: Other ORBIT components (Orchestrator, Memory, MCP tools) need to react to Git events (push completed, branch created, commit made).

**Decision**: Publish all significant Git lifecycle events through `orbit-core`'s `EventBus`. Events are frozen dataclasses extending a `GitEvent` base.

**Rationale**:
- Decouples Git operations from consumers. ORBIT Memory can record operations without ORBIT Git knowing about it.
- Consistent with orbit-execution's streaming event architecture.
- No callbacks — the EventBus is the sole notification mechanism.

**Consequences**: Event emission adds minimal overhead. Events must be designed to carry enough context (repository path, ref names, operation type) to be useful without requiring a back-reference to the engine.

---

## ADR-007: Porcelain Output Parsing

**Context**: Git CLI output varies between human-readable and machine-readable formats.

**Decision**: Always use machine-readable flags when available:
- `git status --porcelain=v2`
- `git log --format=<format>`
- `git diff --raw` or `--numstat`
- `git branch --list --format=<format>`
- `git for-each-ref --format=<format>`

**Rationale**:
- Porcelain output is stable across Git versions.
- Eliminates locale-dependent parsing failures.
- Reduces parser complexity significantly.

**Consequences**: Some operations (e.g., interactive rebase status) don't have porcelain equivalents. Those require careful parsing with defensive error handling.

---

## ADR-008: Hosting Adapters Are External

**Context**: Users will want to interact with GitHub PRs, GitLab MRs, and Azure DevOps work items.

**Decision**: ORBIT Git's public API covers only local Git operations. GitHub, GitLab, Azure DevOps, and Bitbucket adapters are separate engines (e.g., `orbit-github`) that consume ORBIT Git's API.

**Rationale**:
- Keeps ORBIT Git's boundary clean and testable without network dependencies.
- Hosting APIs change frequently; isolating them prevents churn in the core Git engine.
- Different hosting providers have fundamentally different APIs (REST vs GraphQL vs SOAP) that don't share meaningful abstractions.

**Consequences**: ORBIT Git provides the local primitives (push, fetch, remote management) that hosting adapters build upon.
