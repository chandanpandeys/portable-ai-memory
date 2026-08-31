# Contributing to Portable AI Memory

Portable AI Memory is building a vendor-neutral, source-backed memory layer for AI tools. Contributions are welcome across importers, retrieval, MCP integrations, deployment, privacy, testing, and documentation.

## Principles

1. **User-owned memory** — raw memory belongs to the user, not the project or hosting provider.
2. **Lossless source of truth** — derived summaries, embeddings, and graph facts must never replace original source records.
3. **Provenance by default** — derived information should point back to source conversation/message IDs whenever possible.
4. **Portable interfaces** — prefer open formats and protocols over vendor-specific lock-in.
5. **Privacy first** — never commit real user exports, API tokens, databases containing private conversations, or other personal data.

## Development setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,mcp]'
pytest
```

On Windows PowerShell, activate with:

```powershell
.venv\Scripts\Activate.ps1
```

## What to contribute

Good first contribution areas include:

- Claude, Gemini, Codex, and generic Markdown/JSON importers
- Better timestamp and attachment normalization
- PostgreSQL and pgvector persistence
- Hybrid semantic + keyword retrieval
- Temporal knowledge graph integrations
- Additional MCP client setup guides
- Redaction and secret-detection tooling
- Synthetic test fixtures for export edge cases
- Deployment recipes for popular self-hosting platforms

## Pull requests

Keep PRs focused and include tests for behavior changes. Use synthetic fixtures only. If a bug depends on a real conversation export, reduce it to the smallest synthetic reproduction before committing it.

By submitting a contribution, you agree that it is licensed under the Apache License 2.0 used by this project.
