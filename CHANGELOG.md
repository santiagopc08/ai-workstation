# Changelog

All notable changes to the ORBIT Monorepo will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - Milestone 1: ORBIT End-to-End Integration

### Added

- **Developer Experience (DX) Overhaul**:
  - Unified `README.md` documentation across all ORBIT engines (`orbit-core`, `orbit-git`, `orbit-execution`, `orbit-knowledge`, `orbit-skills`).
  - Added global `INSTALL.md` with step-by-step setup instructions via `uv`.
  - Added `QUICKSTART.md` for a 5-minute introduction to running the Repository Summary skill.
  - Added `DOCTOR.md` for troubleshooting engine connections and environment issues.
- **Example Scripts**:
  - `examples/repository_summary.py`
  - `examples/review_changes.py`
  - `examples/search_project.py`
- **Developer Scripts**:
  - `scripts/bootstrap.sh` and `scripts/bootstrap.ps1` for one-click environment setup.
  - `scripts/install.sh` for global installation via `uv tool`.
  - `scripts/dev.sh` to execute the full validation suite (`ruff`, `mypy`, `pytest`) across all packages.

### Fixed
- Fixed formatting and removed dead variables across all projects to ensure 100% compliance with strict linting rules.

### Architecture
- Enforced zero-dependency rule outside of `uv` environments.
- Enforced strict immutability (`dataclasses(frozen=True)`) across all models.
- Established `CapabilityId` resolution pattern for orchestrating engines without tight coupling.
