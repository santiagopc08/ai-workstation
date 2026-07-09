# Architecture Decision Record (ADR) — ORBIT Knowledge

## Context
ORBIT Knowledge is responsible for parsing, indexing, and summarizing local project documentation and source code to provide high-fidelity context for autonomous AI agents. Originally built as an isolated filesystem MCP server, it has been integrated into the ORBIT ecosystem to act as the primary Semantic Knowledge provider.

## Decision 1: Use `fastmcp` and `mcp` for Server Layer
- **Status:** Accepted
- **Rationale:** The Model Context Protocol (MCP) is the emerging standard for connecting AI models to data sources. By implementing the Knowledge Engine as an MCP server, it can be consumed not only by ORBIT's internal `orbit-skills` orchestrator, but also by external tools like Claude Code and Open WebUI seamlessly.

## Decision 2: Local SQLite + Vector Extensions
- **Status:** Accepted
- **Rationale:** To maintain ORBIT's philosophy of zero cloud dependencies, all vector embeddings and metadata must be stored locally. SQLite is lightweight, universally available on macOS, and performs exceptionally well for knowledge bases under 100,000 files when properly tuned.

## Decision 3: Decoupled `GitKnowledgeService`
- **Status:** Accepted
- **Rationale:** `orbit-knowledge` itself does not depend on `orbit-git`. The integration layer (`GitKnowledgeService`) resides in `orbit-git` to aggregate Git context with Knowledge context. This prevents circular dependencies and maintains the isolated responsibilities of each engine.
