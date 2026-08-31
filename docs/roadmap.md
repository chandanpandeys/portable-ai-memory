# Roadmap

Portable AI Memory aims to become a vendor-neutral memory layer that a person can carry across AI products and agents.

## v0.1 — Lossless local memory core

Status: implemented

- ChatGPT export ingestion
- preservation of conversation mapping trees and branches
- exact source text and structured metadata
- source/message integrity hashes
- SQLite FTS retrieval
- exact message lookup
- conversation reconstruction
- bounded context-pack generation
- read-only MCP adapter
- Docker and Vercel deployment scaffolding

## v0.2 — Multi-source import

- Claude conversation importer
- Gemini importer
- Codex/session importer
- generic JSON/Markdown importer SDK
- incremental imports instead of full rebuilds
- attachment normalization and portable source locators
- importer conformance tests

## v0.3 — Cloud persistence and hybrid retrieval

- PostgreSQL canonical store
- pgvector embeddings
- hybrid keyword + semantic ranking
- date/project/source filters
- secret-aware retrieval policies
- migration tooling from SQLite
- authenticated REST + MCP gateway

## v0.4 — Temporal knowledge graph

- entity and project extraction
- decisions, requirements, goals, tools, files, and concepts
- temporal fact history
- superseded decisions and conflict detection
- provenance from graph facts back to exact messages
- Graphiti-compatible integration where useful

## v0.5 — Memory management UI

- private search interface
- project/entity timelines
- inspect exact sources behind derived facts
- context-pack preview and token budgeting
- import status and data-health checks
- privacy/redaction controls

## v1.0 — Portable personal AI memory

- stable importer API
- stable canonical schema
- stable MCP tool contract
- multi-user/self-hosted deployment documentation
- backup/restore and export tooling
- client guides for major MCP-capable AI tools
- reproducible deployment templates

## Non-goals

Portable AI Memory should not become a centralized service that owns everyone's private conversations. The project may support hosted deployment recipes, but the architecture should continue to support self-hosting, private storage, and migration away from any particular provider.
