# Changelog

All notable changes to Portable AI Memory will be documented in this file.

The project follows Semantic Versioning while the public API is evolving. Before `1.0`, minor releases may introduce breaking changes when necessary and will document them here.

## [0.1.0] - 2026-09-01

### Added

- Lossless ChatGPT `chat.html` and `conversations-*.json` import pipeline.
- Canonical JSONL records for conversations, mapping nodes, parent/child edges, messages, and attachment references.
- Exact source/content hashes for integrity and provenance.
- Preservation of ChatGPT conversation branches instead of flattening only the active path.
- SQLite FTS5 retrieval index built from canonical message text.
- Composite `(conversation_id, node_id)` and `(conversation_id, message_id)` identity to safely handle duplicate IDs across conversations.
- Exact message retrieval and full/active conversation reconstruction.
- Source-backed context packs with bounded character budgets and neighboring message expansion.
- Read-only MCP tools: `memory_stats`, `memory_search`, `memory_get_message`, `memory_get_conversation`, and `memory_context_pack`.
- PostgreSQL/pgvector schema for the future cloud persistence layer.
- Docker, Docker Compose, and experimental Vercel deployment scaffolding.
- Apache-2.0 license, contribution guide, security policy, roadmap, and CI.
- Python package metadata for `portable-ai-memory` and support testing across Python 3.10–3.13.

### Security and privacy

- Private exports, SQLite databases, generated canonical data, environment files, and capability-token files are ignored by default.
- The public repository contains software only; user memory remains user-controlled.
- Public bug reports and contributions are expected to use synthetic or redacted fixtures.

### Known limitations

- ChatGPT is the only production importer in this first release.
- Retrieval is currently SQLite FTS5 plus message-graph neighbors; semantic/vector ranking is planned for a later release.
- The temporal knowledge graph described in the architecture is not implemented yet.
- Incremental import/sync is not implemented yet; current imports build a fresh canonical output/index.
- Deployment scaffolding is early-stage and should not be treated as a hardened hosted-memory service.
- MCP support requires the optional `mcp` dependency.

[0.1.0]: https://github.com/chandanpandeys/portable-ai-memory/releases/tag/v0.1.0
