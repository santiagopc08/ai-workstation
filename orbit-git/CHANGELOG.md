# Changelog

All notable changes to the ORBIT Git engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `GitKnowledgeService` as an integration layer between ORBIT Git and ORBIT Knowledge (RFC-014).
- Capability to generate structured markdown summaries for diffs, commits, history, and repository overviews.
- Cross-engine referencing connecting modified code to documentation artifacts via `related_documents()` and `summarize_document()`.

### Added

- `DiffManager` for managing Git diffs (working tree, staged, commits, files) (RFC-013).
- `HistoryManager` for history inspection, logs, and blame (RFC-013).
- `Diff`, `DiffFile`, `DiffStats`, `BlameLine`, and `CommitReference` models.
- Diff and History events (`DiffGenerated`, `HistoryLoaded`, `BlameCompleted`).
- Support for detailed structured parsing of `git diff --numstat`, `git diff --name-status`, and `git blame --line-porcelain`.

### Added

- `RemoteManager` for managing Git remotes (RFC-012).
- `Remote`, `FetchResult`, `PullResult`, `PushResult` models.
- Remote events (`RemoteAdded`, `RemoteRemoved`, `RemoteRenamed`, `FetchCompleted`, `PullCompleted`, `PushCompleted`, `CloneCompleted`).
- Support for `fetch`, `pull`, `push`, `clone`, and `ls-remote` operations.
- `GitValidator.validate_url` for strict security validations to prevent embedded credentials and forbidden protocols like `ext::`.

### Added (Sprint 2: Branches & Commits)
- Full branch management via `BranchManager` (`create`, `delete`, `rename`, `checkout`, `merge`, `rebase`).
- Full commit management via `CommitManager` (`add`, `add_all`, `create`, `amend`, `show`, `cherry_pick`).
- New Domain Models: `Branch`, `Commit`, `MergeResult`, `RebaseResult`.
- Full event publishing via `orbit-core` `EventBus` (`BranchCreated`, `BranchDeleted`, `BranchRenamed`, `BranchCheckedOut`, `MergeCompleted`, `RebaseCompleted`, `CommitCreated`, `CherryPickCompleted`).
- Format-specific parsers in `GitOutputParser` for structured branch, commit, and conflict extraction without relying on fragile regexes.

### Added (Sprint 1: Core Foundation)
- Core architecture mapping (Models, Exceptions, Providers).
- `GitEngine` facade providing public API for repository interactions.
- `RepositoryManager` for domain logic surrounding repositories.
- `GitValidator` for pre-flight repository checks.
- `GitCommandRunner` wrapper that tunnels execution securely through `orbit-execution`'s `ExecutionEngine`.
- `GitOutputParser` with support for parsing `git status --porcelain=v2 --branch` and `git --version`.
- Models: `Repository`, `RepositoryState`, `GitResult`, `GitVersion`, `Status`, `StatusEntry`.
- Exceptions: `GitError`, `RepositoryNotFoundError`, `RepositoryCorruptError`, `GitCommandError`.
- Benchmarks for repository discovery, opening, and status parsing.
- Static analysis and type checking pipelines via `ruff` and `mypy`.
