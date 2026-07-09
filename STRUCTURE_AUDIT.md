# STRUCTURE_AUDIT.md — orbit-knowledge

## Executive Summary

`orbit-knowledge` is the only ORBIT engine that violates every structural convention established by the other four projects (`orbit-core`, `orbit-execution`, `orbit-git`, `orbit-skills`). It is physically located outside the standard engine directory, uses a flat source layout instead of `src/`, is packaged as `knowledge` instead of `orbit_knowledge`, lacks all standard ORBIT documentation artifacts, has no `ruff`/`mypy` tooling configuration, and does not follow the dependency wiring pattern that makes the rest of ORBIT a cohesive monorepo.

The codebase itself is functional and well-architected internally (as confirmed by its own `FINAL_AUDIT.md`), but it is structurally invisible and incompatible with the rest of the platform.

---

## 1. Complete Repository Tree

### Current Location: `/Users/santi/AI/ai-workstation/Python/Servers/orbit-knowledge/`

> **CAUTION:** This is **not** alongside the other engines. All other engines live at `/Users/santi/AI/ai-workstation/orbit-<name>/`.

```
Python/Servers/orbit-knowledge/
├── API.md                          # Root-level (non-standard placement)
├── ARCHITECTURE.md                 # Root-level (non-standard placement)
├── BENCHMARKS.md                   # Root-level (non-standard placement)
├── CHANGELOG.md                    # ✅ Exists (standard)
├── CHUNKING_STRATEGY.md            # Root-level (non-standard — domain-specific)
├── DATABASE_SCHEMA.md              # Root-level (non-standard — domain-specific)
├── EMBEDDING_PIPELINE.md           # Root-level (non-standard — domain-specific)
├── FINAL_AUDIT.md                  # Root-level (non-standard — domain-specific)
├── INDEXER_ARCHITECTURE.md         # Root-level (non-standard — domain-specific)
├── QUALITY_REPORT.md               # ✅ Exists (standard)
├── README.md                       # ⚠️ Exists but uses old naming/content
├── ROADMAP.md                      # Root-level (non-standard — domain-specific)
├── pyproject.toml                  # ⚠️ Exists but missing tooling config
├── uv.lock                         # ✅ Exists
├── docs/
│   ├── API.md                      # Duplicate of root API.md?
│   ├── Architecture.md
│   ├── CLI.md
│   ├── FAQ.md
│   ├── Installation.md
│   ├── Performance.md
│   └── Troubleshooting.md
├── knowledge/                      # ⚠️ Source code (NOT in src/)
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── doctor.py
│   ├── logging_config.py
│   ├── models.py
│   ├── server.py
│   ├── cache/
│   │   └── lru.py
│   ├── fingerprints/
│   │   ├── __init__.py
│   │   └── simhash.py
│   ├── graph/
│   │   ├── __init__.py
│   │   └── engine.py
│   ├── indexing/
│   │   ├── __init__.py
│   │   ├── builder.py
│   │   ├── chunker.py
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── engine.py
│   │   ├── events.py
│   │   ├── hashes.py
│   │   ├── hashing.py
│   │   ├── metadata.py
│   │   ├── queue.py
│   │   ├── scheduler.py
│   │   ├── storage.py
│   │   └── watcher.py
│   ├── mcp/
│   │   ├── prompts.py
│   │   ├── resources.py
│   │   └── tools.py
│   ├── planner/
│   │   ├── __init__.py
│   │   └── query_planner.py
│   ├── providers/
│   │   ├── filesystem.py
│   │   └── markdown.py
│   ├── ranking/
│   │   ├── __init__.py
│   │   └── engine.py
│   ├── search/
│   │   ├── __init__.py
│   │   ├── content.py
│   │   ├── filename.py
│   │   ├── ranking.py
│   │   └── semantic.py
│   ├── services/
│   │   ├── knowledge_service.py
│   │   ├── project_service.py
│   │   └── summary_service.py
│   └── tagging/
│       ├── __init__.py
│       └── tagger.py
├── tests/
│   ├── __init__.py
│   ├── benchmark.py
│   └── test_knowledge.py
├── evaluation/
│   ├── README.md
│   ├── __init__.py
│   ├── benchmark.py
│   ├── evaluator.py
│   ├── generate_questions.py
│   ├── metrics.py
│   ├── questions.yaml
│   ├── runner.py
│   ├── reports/
│   └── scenarios/
├── reports/
│   └── doctor_report.md
└── scratch/                        # Empty
```

### Phantom Location: `/Users/santi/AI/ai-workstation/orbit-knowledge/`

```
orbit-knowledge/
└── README.md                       # ⚠️ Only a README. No source. No pyproject.toml.
```

> **WARNING:** This is a **ghost directory**. It was created during the Milestone 1.0 DX pass to unify READMEs, but it contains no source code and no `pyproject.toml`. It is completely disconnected from the real project. Running `uv sync` here fails.

---

## 2. Differences vs. ORBIT Standard

### 2.1 Physical Location

| Engine | Location | Standard? |
|---|---|---|
| orbit-core | `/ai-workstation/orbit-core/` | ✅ |
| orbit-execution | `/ai-workstation/orbit-execution/` | ✅ |
| orbit-git | `/ai-workstation/orbit-git/` | ✅ |
| orbit-skills | `/ai-workstation/orbit-skills/` | ✅ |
| **orbit-knowledge** | **`/ai-workstation/Python/Servers/orbit-knowledge/`** | **❌** |

### 2.2 Source Layout

| Engine | Layout | Package Name | Standard? |
|---|---|---|---|
| orbit-core | `src/orbit_core/` | `orbit_core` | ✅ |
| orbit-execution | `src/orbit_execution/` | `orbit_execution` | ✅ |
| orbit-git | `src/orbit_git/` | `orbit_git` | ✅ |
| orbit-skills | `src/orbit_skills/` | `orbit_skills` | ✅ |
| **orbit-knowledge** | **`knowledge/`** | **`knowledge`** | **❌** |

> **CRITICAL:** The Python package is named `knowledge`, not `orbit_knowledge`. This means `import orbit_knowledge` fails (as the user experienced). The `orbit-skills` pyproject.toml references the package by path, but the actual import name is `knowledge`, creating a silent mismatch. The `orbit-git` integration layer (`GitKnowledgeService`) works around this by importing from `knowledge` directly — a deviation from the `orbit_*` naming convention.

### 2.3 pyproject.toml

| Feature | Standard (orbit-core) | orbit-knowledge | Match? |
|---|---|---|---|
| `[tool.pytest.ini_options]` | ✅ `testpaths`, `pythonpath` | ❌ Missing | ❌ |
| `[tool.mypy]` (strict) | ✅ Full strict config | ❌ Missing | ❌ |
| `[tool.ruff]` | ✅ Full lint config | ❌ Missing | ❌ |
| `[tool.ruff.lint]` select | ✅ E, F, I, UP, B, SIM | ❌ Missing | ❌ |
| `[tool.ruff.format]` | ✅ lf line ending | ❌ Missing | ❌ |
| `dependencies` | stdlib-only or orbit-* refs | `fastmcp`, `mcp`, `pyyaml`, `starlette` | ⚠️ |
| `[project.optional-dependencies] dev` | ✅ pytest, ruff, mypy | ❌ Missing | ❌ |

### 2.4 Documentation Structure

| Document | core | execution | git | skills | **knowledge** |
|---|---|---|---|---|---|
| `README.md` (unified format) | ✅ | ✅ | ✅ | ✅ | ❌ (old format) |
| `CHANGELOG.md` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `QUALITY_REPORT.md` | ❌ | ✅ | ✅ | ✅ | ✅ |
| `docs/Architecture.md` | ✅ | ✅ | ✅ | ✅ | ✅ (in docs/) |
| `docs/ADR.md` | ❌ | ✅ | ✅ | ✅ | **❌ Missing** |
| `docs/PublicAPI.md` | ❌ | ✅ | ✅ | ✅ | **❌ Missing** |
| `docs/ComponentDiagram.md` | ❌ | ✅ | ✅ | ✅ | **❌ Missing** |
| `docs/Sequence.md` | ❌ | ✅ | ✅ | ✅ | **❌ Missing** |

> **IMPORTANT:** orbit-knowledge has 8 root-level `.md` files (`API.md`, `ARCHITECTURE.md`, `BENCHMARKS.md`, etc.) that should either be consolidated into `docs/` or removed. Some are duplicates of files already inside `docs/`.

### 2.5 Dependency Pattern

| Engine | Depends on orbit-core? | Depends on orbit-execution? | External deps |
|---|---|---|---|
| orbit-core | — | — | None (optional yaml) |
| orbit-execution | ✅ | — | None |
| orbit-git | ✅ | ✅ | None |
| orbit-skills | ✅ | ✅ (via git) | `httpx` |
| **orbit-knowledge** | **❌** | **❌** | `fastmcp`, `mcp`, `pyyaml`, `starlette` |

> **WARNING:** `orbit-knowledge` does **not** depend on `orbit-core`. It has its own independent logging (`logging_config.py`), its own config (`config.py`), its own models (`models.py`), and its own event system (`indexing/events.py`). It is effectively a standalone MCP server that was retrofitted into the ORBIT ecosystem at the reference level only.

### 2.6 Testing & Tooling

| Feature | Standard | orbit-knowledge | Match? |
|---|---|---|---|
| `ruff check` configured | ✅ | ❌ | ❌ |
| `mypy --strict` configured | ✅ | ❌ | ❌ |
| `pytest` testpaths configured | ✅ | ❌ | ❌ |
| Benchmarks separate from tests | ✅ (execution, git) | ❌ `benchmark.py` inside `tests/` | ❌ |
| Evaluation suite | N/A | ✅ `evaluation/` | Unique to knowledge |

---

## 3. Modules That Exist Under Different Names

| ORBIT Standard | orbit-knowledge Equivalent | Notes |
|---|---|---|
| `orbit_core.logging` (`OrbitLogger`) | `knowledge.logging_config` | Own logger, doesn't use `get_logger()` |
| `orbit_core.config` (`SettingsManager`) | `knowledge.config` | Own config system, doesn't use `SettingsManager` |
| `orbit_core.types.models` | `knowledge.models` | Own models, not frozen dataclasses with slots |
| `orbit_core.events` (`EventBus`) | `knowledge.indexing.events` | Own event definitions, not wired to core bus |
| `orbit_core.health` (`HealthChecker`) | `knowledge.doctor` | Own `run_doctor()` function, not registered with `HealthChecker` |

---

## 4. Proposed Reorganization

### Phase 1: Physical Relocation (Zero code changes)

Move the entire project from `Python/Servers/orbit-knowledge/` to `orbit-knowledge/` at the workspace root, replacing the current ghost directory.

### Phase 2: Source Layout Migration

Rename the source directory from `knowledge/` to `src/orbit_knowledge/` to match the `src` layout convention. Update `pyproject.toml` accordingly:
```toml
[tool.hatch.build.targets.wheel]
packages = ["src/orbit_knowledge"]
```

### Phase 3: pyproject.toml Alignment

Add the missing standard tooling sections: `[tool.pytest.ini_options]`, `[tool.mypy]`, `[tool.ruff]`, `[tool.ruff.lint]`, `[tool.ruff.format]`, and `[project.optional-dependencies] dev`.

### Phase 4: Documentation Normalization

1. Move root-level `.md` files (`API.md`, `ARCHITECTURE.md`, `BENCHMARKS.md`, etc.) into `docs/`.
2. Remove duplicates between root and `docs/`.
3. Create the missing standard docs: `docs/ADR.md`, `docs/PublicAPI.md`, `docs/ComponentDiagram.md`, `docs/Sequence.md`.
4. Rewrite `README.md` to follow the unified format (What is it, Requirements, Installation, First Use, Architecture Rules).

### Phase 5: Dependency Wiring (Future — requires code changes)

Wire `orbit-knowledge` into `orbit-core`:
- Replace `knowledge.logging_config` with `orbit_core.logging.get_logger()`.
- Replace `knowledge.config` with `orbit_core.config.SettingsManager`.
- Wire `knowledge.indexing.events` into `orbit_core.events.EventBus`.
- Register `knowledge.doctor` into `orbit_core.health.HealthChecker`.

> **IMPORTANT:** Phase 5 is **out of scope** for this milestone. It requires code changes and is listed here for planning purposes only.

---

## 5. Impact Estimate

| Phase | Files Affected | Risk | Breaks Imports? | Breaks Tests? |
|---|---|---|---|---|
| 1. Physical Relocation | 0 (move only) | Low | ✅ Yes — all `file:///` refs in `pyproject.toml` across orbit-git and orbit-skills | No |
| 2. Source Layout | ~45 `.py` files | Medium | ✅ Yes — `import knowledge` → `import orbit_knowledge` everywhere | ✅ Yes |
| 3. pyproject.toml | 1 file | None | No | No |
| 4. Documentation | ~15 `.md` files | None | No | No |
| 5. Dependency Wiring | ~8 `.py` files | High | No (additive) | Possibly |

### Downstream Impact of Phases 1+2

The following files reference `orbit-knowledge` by path or import name and would need updates:

| File | Reference Type |
|---|---|
| `orbit-git/pyproject.toml` | `file:///...Python/Servers/orbit-knowledge` |
| `orbit-skills/pyproject.toml` | `file:///...Python/Servers/orbit-knowledge` |
| `orbit-git/src/orbit_git/integration.py` | `from knowledge...` (if any direct import) |
| `orbit-skills/src/orbit_skills/bootstrap.py` | `from orbit_git.integration import GitKnowledgeService` (indirect) |
| `scripts/bootstrap.sh` | References `orbit-knowledge` by directory name |
| `scripts/dev.sh` | References `orbit-knowledge` by directory name |

---

## 6. Summary of Findings

| Category | Count |
|---|---|
| **Critical structural violations** | 3 (wrong location, wrong source layout, wrong package name) |
| **Missing documentation artifacts** | 4 (ADR, PublicAPI, ComponentDiagram, Sequence) |
| **Missing tooling config** | 3 (ruff, mypy, pytest sections in pyproject.toml) |
| **Modules duplicating orbit-core** | 5 (logging, config, models, events, health) |
| **Root-level docs to consolidate** | 8 (should move to docs/) |
| **Ghost directory to clean up** | 1 (`/ai-workstation/orbit-knowledge/` with only a README) |
