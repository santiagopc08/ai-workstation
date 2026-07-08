# Changelog

All notable changes to the ORBIT Git engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
