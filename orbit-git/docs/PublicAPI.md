# ORBIT Git: Public API

This document defines the strict, public API contract for ORBIT Git. It contains no external dependencies beyond `orbit-core` and `orbit-execution`.

---

## 1. Core Interfaces

### `GitEngine`
- **Purpose**: The main entry point for all Git operations in the ORBIT platform.
- **Responsibilities**: Open/close repositories, delegate to domain managers, coordinate observability.
- **Constructor Parameters**:
  - `execution_engine: ExecutionEngine`
  - `event_bus: EventBus | None = None`
  - `logger: Logger | None = None`
  - `metrics: MetricsCollector | None = None`
  - `registry: ComponentRegistry | None = None`
- **Methods**:
  - `open(path: str) -> Repository` — Validate and open a Git repository.
  - `close(repo: Repository) -> None` — Release a repository handle.
  - `branches(repo: Repository) -> BranchManager` — Access branch operations.
  - `commits(repo: Repository) -> CommitManager` — Access commit operations.
  - `remotes(repo: Repository) -> RemoteManager` — Access remote operations.
  - `tags(repo: Repository) -> TagManager` — Access tag operations.
  - `worktrees(repo: Repository) -> WorktreeManager` — Access worktree operations.
  - `submodules(repo: Repository) -> SubmoduleManager` — Access submodule operations.
  - `config(repo: Repository) -> GitConfigManager` — Access Git configuration.
  - `status(repo: Repository) -> Status` — Get working tree status.
  - `diff(repo: Repository, ref_a: str | None = None, ref_b: str | None = None, staged: bool = False) -> Diff` — Produce a diff.
  - `log(repo: Repository, max_count: int = 50, ref: str = "HEAD") -> list[Commit]` — Read commit history.
  - `blame(repo: Repository, path: str, ref: str = "HEAD") -> list[BlameLine]` — Annotate file lines.
  - `stash_list(repo: Repository) -> list[Stash]` — List stashes.
  - `stash_save(repo: Repository, message: str = "") -> Stash` — Save working directory to stash.
  - `stash_pop(repo: Repository, index: int = 0) -> None` — Pop a stash.
  - `stash_drop(repo: Repository, index: int = 0) -> None` — Drop a stash.
  - `stash_apply(repo: Repository, index: int = 0) -> None` — Apply a stash without removing it.
  - `restore(repo: Repository, paths: list[str], source: str | None = None, staged: bool = False) -> None` — Restore files.
  - `reset(repo: Repository, ref: str = "HEAD", mode: ResetMode = ResetMode.MIXED) -> None` — Reset HEAD.
  - `clean(repo: Repository, force: bool = False, directories: bool = False, ignored: bool = False) -> list[str]` — Clean untracked files.
- **Invariants**: Every method that accepts a `Repository` validates that the handle is still open. All methods delegate Git execution to `GitCommandRunner`.

### `GitProvider` (Protocol)
- **Purpose**: SPI for Git execution backends.
- **Responsibilities**: Build and execute Git commands against a repository.
- **Methods**:
  - `run(repo_path: str, args: list[str], env: dict[str, str] | None = None) -> GitResult`
  - `version() -> str`
- **Relationships**: Internal to `GitEngine`. Users never interact with providers directly.

### `LocalGitProvider`
- **Purpose**: Default provider that executes Git via the local `git` binary through `ExecutionEngine`.
- **Implements**: `GitProvider`

---

## 2. Domain Managers

### `BranchManager`
- **Methods**:
  - `list(include_remote: bool = False) -> list[Branch]`
  - `current() -> Branch | None`
  - `create(name: str, start_point: str = "HEAD") -> Branch`
  - `delete(name: str, force: bool = False) -> None`
  - `rename(old_name: str, new_name: str) -> Branch`
  - `checkout(name: str, create: bool = False) -> Branch`
  - `merge(source: str, no_ff: bool = False, message: str | None = None) -> MergeResult`
  - `rebase(upstream: str, interactive: bool = False) -> RebaseResult`

### `CommitManager`
- **Methods**:
  - `create(message: str, all: bool = False, amend: bool = False) -> Commit`
  - `show(ref: str = "HEAD") -> Commit`
  - `cherry_pick(ref: str) -> Commit`
  - `add(paths: list[str]) -> None`
  - `add_all() -> None`

### `RemoteManager`
- **Methods**:
  - `list() -> list[Remote]`
  - `add(name: str, url: str) -> Remote`
  - `remove(name: str) -> None`
  - `rename(old_name: str, new_name: str) -> Remote`
  - `fetch(remote: str = "origin", prune: bool = False) -> None`
  - `pull(remote: str = "origin", branch: str | None = None, rebase: bool = False) -> None`
  - `push(remote: str = "origin", branch: str | None = None, force: bool = False, tags: bool = False) -> None`

### `TagManager`
- **Methods**:
  - `list() -> list[Tag]`
  - `create(name: str, ref: str = "HEAD", message: str | None = None, annotated: bool = True) -> Tag`
  - `delete(name: str) -> None`

### `WorktreeManager`
- **Methods**:
  - `list() -> list[Worktree]`
  - `add(path: str, branch: str | None = None) -> Worktree`
  - `remove(path: str, force: bool = False) -> None`

### `SubmoduleManager`
- **Methods**:
  - `list() -> list[Submodule]`
  - `init() -> None`
  - `update(recursive: bool = True) -> None`
  - `sync() -> None`
  - `status() -> list[Submodule]`

### `GitConfigManager`
- **Methods**:
  - `get(key: str, scope: ConfigScope = ConfigScope.LOCAL) -> str | None`
  - `set(key: str, value: str, scope: ConfigScope = ConfigScope.LOCAL) -> None`
  - `unset(key: str, scope: ConfigScope = ConfigScope.LOCAL) -> None`
  - `list_all(scope: ConfigScope = ConfigScope.LOCAL) -> dict[str, str]`

---

## 3. Models & Records

### `Repository`
- **Purpose**: Handle to an opened, validated Git repository.
- **Properties**: `path: str`, `real_path: str`, `is_bare: bool`, `state: RepositoryState`.

### `RepositoryState` (Enum)
- Values: `CLEAN`, `MERGING`, `REBASING`, `CHERRY_PICKING`, `REVERTING`, `BISECTING`, `DETACHED_HEAD`.

### `Branch`
- **Properties**: `name: str`, `ref: str`, `is_remote: bool`, `is_current: bool`, `upstream: str | None`, `ahead: int`, `behind: int`.

### `Commit`
- **Properties**: `hash: str`, `short_hash: str`, `author: str`, `author_email: str`, `date: str`, `message: str`, `parent_hashes: list[str]`.

### `Tag`
- **Properties**: `name: str`, `ref: str`, `is_annotated: bool`, `message: str`, `tagger: str | None`.

### `Remote`
- **Properties**: `name: str`, `fetch_url: str`, `push_url: str`.

### `Diff`
- **Properties**: `files: list[DiffFile]`, `stats: DiffStats`.

### `DiffFile`
- **Properties**: `path: str`, `old_path: str | None`, `status: DiffFileStatus`, `insertions: int`, `deletions: int`.

### `DiffFileStatus` (Enum)
- Values: `ADDED`, `MODIFIED`, `DELETED`, `RENAMED`, `COPIED`, `UNMERGED`.

### `DiffStats`
- **Properties**: `files_changed: int`, `insertions: int`, `deletions: int`.

### `Status`
- **Properties**: `staged: list[StatusEntry]`, `unstaged: list[StatusEntry]`, `untracked: list[str]`, `branch: str`, `upstream: str | None`, `ahead: int`, `behind: int`.

### `StatusEntry`
- **Properties**: `path: str`, `status: str`, `old_path: str | None`.

### `Stash`
- **Properties**: `index: int`, `message: str`, `ref: str`.

### `Worktree`
- **Properties**: `path: str`, `head: str`, `branch: str | None`, `is_bare: bool`, `is_detached: bool`, `is_locked: bool`.

### `Submodule`
- **Properties**: `name: str`, `path: str`, `url: str`, `branch: str | None`, `hash: str`, `is_initialized: bool`.

### `BlameLine`
- **Properties**: `line_number: int`, `commit_hash: str`, `author: str`, `date: str`, `content: str`.

### `MergeResult`
- **Properties**: `success: bool`, `conflicts: list[str]`, `commit: Commit | None`.

### `RebaseResult`
- **Properties**: `success: bool`, `conflicts: list[str]`, `applied_commits: int`.

### `GitResult`
- **Purpose**: Internal result from `GitCommandRunner`.
- **Properties**: `success: bool`, `stdout: str`, `stderr: str`, `exit_code: int`, `duration_ms: int`.

### `GitOperation` (Enum)
- Values: `STATUS`, `DIFF`, `LOG`, `BLAME`, `COMMIT`, `BRANCH_CREATE`, `BRANCH_DELETE`, `CHECKOUT`, `MERGE`, `REBASE`, `FETCH`, `PULL`, `PUSH`, `TAG_CREATE`, `TAG_DELETE`, `STASH_SAVE`, `STASH_POP`, `RESET`, `CLEAN`, `RESTORE`, `CHERRY_PICK`, `CONFIG_GET`, `CONFIG_SET`, `WORKTREE_ADD`, `WORKTREE_REMOVE`, `SUBMODULE_INIT`, `SUBMODULE_UPDATE`.

### Enums

#### `ResetMode`
- Values: `SOFT`, `MIXED`, `HARD`.

#### `ConfigScope`
- Values: `LOCAL`, `GLOBAL`, `SYSTEM`.

---

## 4. Events (EventBus)

All events are frozen dataclasses with `slots=True`. They extend a `GitEvent` base.

### `GitEvent` (Base)
- **Properties**: `repo_path: str`, `operation: GitOperation`, `timestamp: float`.

### Events:

| Event | Additional Properties |
|---|---|
| `RepositoryOpened` | `is_bare: bool` |
| `RepositoryClosed` | — |
| `FetchCompleted` | `remote: str` |
| `PullCompleted` | `remote: str`, `branch: str` |
| `PushCompleted` | `remote: str`, `branch: str` |
| `CommitCreated` | `hash: str`, `message: str` |
| `BranchCreated` | `name: str`, `start_point: str` |
| `BranchDeleted` | `name: str` |
| `MergeCompleted` | `source: str`, `success: bool`, `conflicts: list[str]` |
| `RebaseCompleted` | `upstream: str`, `success: bool` |
| `TagCreated` | `name: str`, `ref: str` |

---

## 5. Exceptions

All exceptions extend `GitError`, which extends `orbit-core`'s `OrbitError`.

| Exception | When |
|---|---|
| `GitError` | Base for all ORBIT Git failures. |
| `RepositoryNotFoundError` | Path is not a Git repository. |
| `RepositoryCorruptError` | Repository is missing essential Git internals. |
| `GitCommandError` | A Git command exited with non-zero. Contains `exit_code`, `stderr`. |
| `MergeConflictError` | Merge or rebase produced unresolved conflicts. |
| `BranchNotFoundError` | Referenced branch does not exist. |
| `RemoteNotFoundError` | Referenced remote does not exist. |
| `DetachedHeadError` | Operation requires a branch but HEAD is detached (only for destructive ops requiring explicit confirmation). |

---

## 6. Capabilities

The engine registers granular capabilities via `orbit-core` Registry:

| Capability ID | Description |
|---|---|
| `git.repository` | Can discover and validate repositories. |
| `git.branch` | Can manage branches. |
| `git.commit` | Can create and inspect commits. |
| `git.remote` | Can manage remotes (fetch, pull, push). |
| `git.tag` | Can manage tags. |
| `git.diff` | Can produce diffs. |
| `git.stash` | Can manage stashes. |
| `git.worktree` | Can manage worktrees. |
| `git.submodule` | Can manage submodules. |
| `git.config` | Can read/write Git configuration. |
