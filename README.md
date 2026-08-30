# Portable AI Memory

A lossless, source-backed memory layer that lets multiple AI clients use the same conversation history without depending on one vendor account's built-in memory.

## What it does

- Imports ChatGPT `chat.html` exports or `conversations-*.json` shards.
- Preserves every conversation mapping node and parent/child branch.
- Keeps exact message text plus the original content and metadata JSON.
- Builds a local SQLite FTS5 retrieval index without replacing canonical source records.
- Reconstructs active conversation branches.
- Builds bounded, source-backed context packs.
- Exposes read-only MCP tools for ChatGPT-compatible MCP clients, Claude, Codex, Hermes, Cursor, and other MCP clients.
- Includes a PostgreSQL/pgvector schema for the next cloud-storage stage.

## Privacy model

**This repository is code only.** Never commit chat exports, canonical JSONL, SQLite databases, embeddings containing private content, capability tokens, or deployment secrets. The included `.gitignore` blocks the common private-data paths.

The source archive remains the immutable source of truth. Embeddings, summaries, graph facts, and context packs are derived indexes and must retain provenance to source message IDs.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[mcp]'
python scripts/import_chatgpt.py /path/to/chat.html ./output
python -m memory_os.search ./output/memory.sqlite 'your query' --limit 10
```

Run the MCP server:

```bash
MEMORY_DB_PATH=./output/memory.sqlite python -m memory_os.mcp_server
```

The core MCP tools are:

- `memory_stats`
- `memory_search`
- `memory_get_message`
- `memory_get_conversation`
- `memory_context_pack`

## Architecture

```text
Immutable exports
      ↓
Canonical messages + branch graph
      ↓
Retrieval index + temporal knowledge graph
      ↓
Context-pack builder
      ↓
Read-only MCP / REST gateway
      ↓
ChatGPT / Claude / Codex / Hermes / other agents
```

See [`docs/architecture.md`](docs/architecture.md) for details.

## Current status

Phase 1 implements canonical import, branch preservation, integrity hashes, SQLite FTS retrieval, exact-message lookup, conversation reconstruction, context packs, and the MCP adapter. PostgreSQL/vector search and the temporal graph layer are the next stages.
