# Portable AI Memory

**One memory layer for all your AI tools.**

## About

Portable AI Memory is an open-source, privacy-first memory layer for AI. It helps people preserve their conversation history, decisions, projects, and long-term context in a vendor-neutral format, then reuse that memory across tools such as ChatGPT, Claude, Gemini, Codex, Cursor, Hermes, and other MCP-compatible agents.

The project is built around a simple principle: **your AI memory should belong to you**. Original conversations remain the source of truth, while search indexes, context packs, embeddings, summaries, and knowledge graphs are treated as rebuildable derived layers. The software can be public and collaborative while every user's actual memory remains private and self-owned.

Portable AI Memory is an open-source, vendor-neutral, source-backed memory system that lets people carry their conversation history, decisions, projects, and context across AI products without depending on one provider's built-in memory.

The long-term goal is simple:

> Your AI history should belong to you, remain portable, and be usable by any agent you choose.

## Why this exists

Today, useful context is fragmented across ChatGPT, Claude, Gemini, coding agents, CLIs, notes, and other tools. Switching accounts or models often means losing years of accumulated context.

Portable AI Memory separates **memory from the AI vendor**. Original messages remain the source of truth; search indexes, embeddings, summaries, graph facts, and context packs are derived layers that can be rebuilt.

## What works today

- Imports ChatGPT `chat.html` exports or `conversations-*.json` shards.
- Preserves every conversation mapping node and parent/child branch.
- Keeps exact message text plus the original content and metadata JSON.
- Generates source/message integrity hashes.
- Builds a local SQLite FTS5 retrieval index without replacing canonical source records.
- Reconstructs active conversation branches.
- Builds bounded, source-backed context packs.
- Exposes read-only MCP tools for ChatGPT-compatible MCP clients, Claude, Codex, Hermes, Cursor, and other MCP clients.
- Includes a PostgreSQL/pgvector schema for the next cloud-storage stage.
- Includes Docker and cloud-deployment scaffolding.

## Core principles

1. **User-owned memory** — users control where their private corpus lives.
2. **Lossless source of truth** — original messages are preserved instead of replaced by summaries.
3. **Provenance** — derived facts should point back to exact source messages.
4. **Vendor neutrality** — memory should survive switching models, accounts, or AI products.
5. **Open protocols** — MCP, portable schemas, and standard databases are preferred over lock-in.
6. **Privacy first** — the project code can be public while each person's memory remains private.

## Privacy model

**This repository contains software, not user memory.** Never commit chat exports, canonical JSONL, SQLite databases, embeddings containing private content, capability tokens, or deployment secrets. The included `.gitignore` blocks common private-data paths.

A person's source archive remains their immutable source of truth. Embeddings, summaries, graph facts, search indexes, and context packs are derived data and should retain provenance to source message IDs.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[mcp]'
python scripts/import_chatgpt.py /path/to/chat.html ./output
python -m memory_os.search ./output/memory.sqlite 'your query' --limit 10
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Run the MCP server:

```bash
MEMORY_DB_PATH=./output/memory.sqlite python -m memory_os.mcp_server
```

## MCP tools

- `memory_stats`
- `memory_search`
- `memory_get_message`
- `memory_get_conversation`
- `memory_context_pack`

The most important higher-level primitive is `memory_context_pack`: instead of sending an entire lifetime of conversations to an AI, it selects a bounded set of relevant source-backed context for the current task.

## Architecture

```text
ChatGPT / Claude / Gemini / agents / notes
                  ↓
             Importers
                  ↓
        Immutable source records
                  ↓
      Canonical messages + branches
                  ↓
       Keyword + semantic retrieval
                  ↓
        Temporal knowledge graph
                  ↓
          Context-pack builder
                  ↓
          Read-only MCP / API
                  ↓
 ChatGPT / Claude / Codex / Hermes / Cursor / others
```

See [`docs/architecture.md`](docs/architecture.md) for the current design and [`docs/roadmap.md`](docs/roadmap.md) for planned milestones.

## Roadmap highlights

- Claude, Gemini, Codex, and generic importers
- incremental syncing
- PostgreSQL + pgvector hybrid retrieval
- temporal knowledge graph with provenance
- conflict and superseded-decision detection
- private memory-management UI
- one-click/self-hosted deployment recipes
- stable cross-client MCP interface

## Contributing

Contributions are welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md). Please use **synthetic fixtures only** in public issues and pull requests; never upload private conversation exports.

Security guidance is in [`SECURITY.md`](SECURITY.md).

## License

Apache License 2.0. See [`LICENSE`](LICENSE).

## Current status

Portable AI Memory is in early development. The v0.1 core implements lossless ChatGPT import, branch preservation, integrity hashes, SQLite FTS retrieval, exact-message lookup, conversation reconstruction, context packs, MCP access, and deployment scaffolding. The next major milestone is multi-source import plus cloud-backed hybrid retrieval.
