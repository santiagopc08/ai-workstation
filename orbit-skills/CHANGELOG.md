# Changelog

All notable changes to ORBIT Skills will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — MILESTONE-001

### Added

- Package foundation (`orbit-skills`) with dependencies on `orbit-core`, `orbit-git`, `orbit-execution`, `orbit-knowledge`, `httpx`.
- Core models: `SkillId`, `CapabilityId`, `SkillCategory`, `SkillCapability`, `SkillMetadata`, `SkillInput`, `SkillOutput`, `SkillError`, `SkillRequest`, `SkillResult`.
- Concrete I/O types: `RepositorySummaryInput/Output`, `ReviewChangesInput/Output`, `ExplainCommitInput/Output`, `SearchProjectInput/Output`.
- `CapabilityRegistry` for generic capability resolution (no hardcoded engine refs).
- `OrbitSkillContext` implementing `SkillContext` protocol with `resolve(CapabilityId)`.
- `SkillRegistry` for skill discovery and registration.
- `SkillValidator` for pre-execution request validation.
- `SkillExecutor` with full observability (events, logging, timing).
- Execution events: `SkillExecutionStarted`, `SkillExecutionCompleted`, `SkillExecutionFailed`.
- `LLMClient` for LM Studio OpenAI-compatible API integration.
- Skills: `RepositorySummarySkill`, `ReviewChangesSkill`, `ExplainCommitSkill`, `SearchProjectSkill`.
- `OrbitBootstrap` for runtime initialization.
- `demo_repository_summary.py` demo script.
- End-to-end integration tests (real Git, mocked LLM).
