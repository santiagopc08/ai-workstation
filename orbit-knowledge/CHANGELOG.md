# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-07-06

### Added
- Integrated Query Planner supporting `HYBRID`, `GRAPH`, `READ_FILE`, and `MULTI_STAGE` routing strategies.
- Knowledge Graph module (`knowledge/graph/engine.py`) storing technology vertices and relational edges in SQLite.
- Custom SimHash fingerprinting (`knowledge/fingerprints/simhash.py`) for lightning-fast duplicate checking.
- Automated Tagging Engine (`knowledge/tagging/tagger.py`) detecting categories and tech stacks from files rules.
- Optional observability endpoint `/health` on FastMCP.
- Hot diagnostics checks subcommand `orbit-knowledge doctor`.
- Validation and benchmark suite (`evaluation/runner.py`) scoring Recall, Precision, and scale thresholds.
- Standardized packaging structure (`pyproject.toml`) and `orbit-knowledge` entrypoint script.

### Changed
- Migrated codebase imports from top-level namespace `mcp` to standard `knowledge.mcp` to resolve package collisions.
- Refactored `config.py` loading precedence to respect CLI -> ENV -> YAML -> Defaults.

---

## [2.0.0] - 2026-06-15

### Added
- Decoupled SQLite storage engine away from the raw filesystem layer.
- Added support for index reconstruction and background polling watchers.

---

## [1.0.0] - 2026-05-10

### Added
- Functional `orbit-filesystem` MCP server supporting `list_files` and `read_file`.
