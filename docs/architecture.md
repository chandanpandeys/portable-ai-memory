# Architecture

Source Zero (immutable exports) → Canonical Memory → Retrieval Index + Temporal Graph → Context Builder → MCP/REST.

Canonical Memory is the contract between importers and every future subsystem. A ChatGPT/Claude/Codex importer may change, but downstream tools always receive the same canonical objects.

## Retrieval rule

A request is answered by combining:

1. exact/full-text search,
2. semantic/vector search,
3. graph expansion,
4. chronology and supersession,
5. source-message reconstruction.

The context builder returns a bounded context pack with exact source passages and provenance instead of attempting to send an entire lifetime archive to a model.
