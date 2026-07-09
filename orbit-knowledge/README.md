# ORBIT Knowledge

The structured documentation and context extraction engine for the ORBIT platform.

## What is ORBIT Knowledge?

`orbit-knowledge` parses, indexes, and summarizes local projects and their documentation. It provides AI agents with high-fidelity, context-aware information about project structure, architectural decisions, and recent changes. 

It exposes integration adapters like `GitKnowledgeService` (via `orbit-git`) which seamlessly merges Git repository state with underlying project documentation, acting as a context aggregator for higher-level orchestrators. It also functions as a standalone MCP server for external clients like Open WebUI.

## Requirements

- **Python:** 3.10 or higher.
- **Package Manager:** `uv`

## Installation

```bash
uv sync
```

## First Use

```python
from orbit_knowledge.search.semantic import SemanticSearch
from orbit_knowledge.indexing.builder import IndexBuilder

# Initialize the indexing builder
builder = IndexBuilder("/path/to/repo")
builder.build_index()

# Perform a semantic search
searcher = SemanticSearch("/path/to/repo")
results = searcher.search("How does authentication work?", top_k=3)

for result in results:
    print(result.file_path, result.score)
```

## Architecture Rules

- **Zero Cloud Dependencies:** All embeddings, vectors, and indexes must be generated and stored strictly locally (SQLite/FAISS) to preserve privacy and offline capabilities.
- **Isolated Integration:** While `orbit-knowledge` is part of the ORBIT platform, it currently maintains isolated data models and logging to preserve its standalone MCP server capabilities. (Phase 5 integration is deferred).
- **Public API Boundary:** External consumers must only interact with Knowledge through public service interfaces, never by parsing internal SQLite databases directly.
