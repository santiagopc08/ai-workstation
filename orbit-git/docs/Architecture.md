# ORBIT Git Architecture

## 1. Context and Vision

ORBIT Git is the engine responsible for all Git interactions across the ORBIT platform. It is the **exclusive gateway** for repository operations: no other ORBIT component may invoke `git` commands directly. Every Git operation is routed through `orbit-execution`'s `ExecutionEngine`, inheriting its security policies, sandboxing, streaming, and observability transparently.

ORBIT Git does not use GitPython, pygit2, or any external Git library. It operates entirely by constructing `ExecutionRequest` payloads containing `git` CLI commands and interpreting the structured output returned via `ExecutionResult`.

## 2. Responsibilities

### What ORBIT Git DOES:
- Discovers and validates Git repositories on disk.
- Manages branches (create, delete, rename, checkout, list).
- Manages commits (create, amend, cherry-pick, log, show, blame).
- Manages tags (create, delete, list, push).
- Manages remotes (add, remove, rename, list, fetch, pull, push).
- Reports repository status (working tree changes, staged files, untracked files).
- Produces diffs (staged, unstaged, between refs).
- Manages stashes (save, pop, list, drop, apply).
- Manages worktrees (add, remove, list).
- Manages submodules (init, update, status, sync).
- Reads and writes Git configuration (local, global, system).
- Performs merge, rebase, restore, reset, and clean operations.

### What ORBIT Git does NOT do:
- **No direct subprocess calls.** Every command passes through `ExecutionEngine`.
- **No Git hosting logic.** It does not know about GitHub PRs, GitLab MRs, or Azure DevOps pipelines. Future hosting adapters will consume ORBIT Git's API, not the reverse.
- **No file content parsing.** It does not parse source code, resolve conflicts automatically, or apply semantic diffs. That is ORBIT Workflow's or an LLM agent's responsibility.
- **No credential management.** It does not store, rotate, or provision SSH keys or tokens. It relies on the host's configured credential helpers and SSH agent.
- **No LLM integration.** It does not generate commit messages, summarize diffs, or perform AI-assisted rebasing.

## 3. Dependencies

| Dependency | Purpose |
|---|---|
| `orbit-core` | Interfaces, EventBus, Logger, Health, Registry, Config, Exceptions, Types |
| `orbit-execution` | ExecutionEngine, ExecutionRequest, ExecutionResult, ExecutionPolicy |
| Python Standard Library | `os`, `pathlib`, `json`, `re`, `dataclasses`, `enum` |

No other dependencies are permitted.

## 4. Internal Architecture

ORBIT Git follows a **Manager-per-domain** decomposition. Each domain (branches, commits, remotes, etc.) is encapsulated in a dedicated manager class that knows how to build the correct `git` CLI arguments and parse the output. All managers share a common `GitCommandRunner` that wraps `ExecutionEngine`.

### Layer Diagram

```
┌──────────────────────────────────────────────────────┐
│                      GitEngine                        │
│              (Facade / Public Entry Point)             │
├──────────────────────────────────────────────────────┤
│  RepositoryManager │ BranchManager │ CommitManager    │
│  RemoteManager     │ WorktreeManager│ SubmoduleManager│
│  GitConfigManager  │ GitValidator   │ TagManager      │
├──────────────────────────────────────────────────────┤
│                  GitCommandRunner                     │
│          (Translates domain calls → ExecutionRequest)  │
├──────────────────────────────────────────────────────┤
│               orbit-execution (ExecutionEngine)        │
├──────────────────────────────────────────────────────┤
│               orbit-core (EventBus, Logger, Health)    │
└──────────────────────────────────────────────────────┘
```

### GitCommandRunner

This is the **single internal class** that interacts with `ExecutionEngine`. It:
- Constructs `ExecutionRequest` payloads with `command=["git", ...args]`.
- Sets `cwd` to the repository root.
- Applies a default `ExecutionPolicy` that restricts CWD to the repository boundary.
- Interprets `ExecutionResult` and translates non-zero exit codes into typed `GitError` exceptions.
- Optionally injects `GIT_DIR`, `GIT_WORK_TREE`, and `GIT_CONFIG_NOSYSTEM` environment variables for isolation.

### GitValidator

Performs pre-flight validation before any Git operation:
- Verifies the target path is a valid Git repository (contains `.git/` or is bare).
- Resolves symlinks via `os.path.realpath` to prevent path traversal escapes.
- Validates that the repository is not in a corrupt state (missing `HEAD`, missing `objects/`).
- Detects bare vs non-bare repositories to prevent destructive operations on bare repos.
- Checks for detached HEAD state and reports it as metadata (not an error).

## 5. Security Architecture

| Threat | Mitigation |
|---|---|
| **Path Traversal** | `GitValidator` resolves all paths with `os.path.realpath()` before passing to `ExecutionEngine`. The sandbox layer in orbit-execution provides a second barrier. |
| **Bare Repository Abuse** | `RepositoryManager` detects bare repos and disallows checkout/commit/stash operations. |
| **Detached HEAD** | Reported as metadata in `Repository.state`. Destructive operations on detached HEAD require explicit confirmation flags. |
| **Repository Corruption** | `GitValidator` checks for essential Git internals (`HEAD`, `objects/`, `refs/`). Operations on corrupt repos raise `RepositoryCorruptError`. |
| **Invalid Remotes** | `RemoteManager` validates remote URLs against a basic syntax check. No `file://` protocol remotes are allowed by default (configurable). |
| **Credential Leakage** | `GitCommandRunner` strips `GIT_ASKPASS` and credential-related environment variables by default. `ExecutionPolicy.env_blacklist` provides the enforcement layer. |
| **Unsafe Working Directories** | Inherits `SandboxManager` enforcement from orbit-execution: `allowed_cwds` restricts operations to sanctioned directory trees. |

## 6. Observability

| Concern | Integration |
|---|---|
| **Structured Logging** | `GitEngine` instantiates an `OrbitLogger` via `get_logger("git")`. Every operation logs the repository path, command, and duration. |
| **Health** | `GitEngine` exposes a `HealthReporter` compatible with `orbit-core.HealthCheck`. Reports Git binary version, number of open repositories, and active operations. |
| **Metrics** | Operations are tracked via `MetricsCollector`: `git.operations.total`, `git.operations.failed`, `git.fetch.duration_ms`, etc. |
| **Events** | All lifecycle transitions are published to `EventBus` (see Events section in PublicAPI.md). |
| **Registry** | `GitEngine` registers itself under `engine.git` in `ComponentRegistry`. Health is registered under `health.git`. |

## 7. Extensibility

ORBIT Git is designed to be consumed by future hosting adapters (GitHub, GitLab, Azure DevOps, Bitbucket) without modification to its public API. The hosting layer will:
- Use `RemoteManager` to configure and interact with remotes.
- Use `BranchManager` and `CommitManager` for local operations.
- Add its own hosting-specific types (PullRequest, MergeRequest, Pipeline) outside ORBIT Git's boundary.

The `GitProvider` protocol allows future non-CLI backends (e.g., a `LibGit2Provider` via FFI) to replace `LocalGitProvider` without changing the engine's public surface.

## 8. Cross-Platform Compatibility

| Concern | Strategy |
|---|---|
| **Git Binary Location** | Resolved via `shutil.which("git")`. `GitValidator` checks for Git availability at engine startup. |
| **Path Separators** | All internal paths use `pathlib.PurePosixPath` for Git ref operations and `pathlib.Path` for filesystem operations. `os.sep` is never hardcoded. |
| **Line Endings** | Git output parsing uses universal newline mode. `autocrlf` configuration is respected but not managed. |
| **Symlinks** | Always resolved via `os.path.realpath()` before any operation. |

## 9. Architectural Risks & Mitigations

| Risk | Mitigation |
|---|---|
| **Git CLI Output Format Changes** | Pin parsing to `--porcelain` or `--format` flags wherever available. Use `--no-optional-locks` to avoid lock contention. |
| **Large Repository Performance** | Provide `--no-walk`, `--max-count`, and `--sparse` options in manager methods. Never load full history by default. |
| **Concurrent Operations** | Each operation creates an independent `ExecutionRequest`. Git's own lockfile mechanism (`index.lock`) handles concurrency at the filesystem level. ORBIT Git does not add additional locking. |
| **Encoding Issues** | Default to UTF-8. Provide encoding overrides via `ExecutionOptions.encoding` for repositories with non-UTF-8 paths. |
