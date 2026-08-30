"""Remote read-only MCP gateway for Portable Memory OS.

Requires the official Model Context Protocol Python SDK:
    pip install 'mcp>=1.12.4,<2'

Run:
    MEMORY_DB_PATH=/data/memory.sqlite python -m memory_os.mcp_server

The Streamable HTTP endpoint is served by the MCP SDK (commonly /mcp).
"""
from __future__ import annotations

import os
from pathlib import Path

from mcp.server import MCPServer

from .service import MemoryService

DB_PATH = Path(os.environ.get("MEMORY_DB_PATH", "./output/memory.sqlite"))
service = MemoryService(DB_PATH)
mcp = MCPServer("Portable Memory OS")


@mcp.tool()
def memory_stats() -> dict:
    """Return high-level counts for the connected personal memory archive."""
    return service.stats()


@mcp.tool()
def memory_search(query: str, limit: int = 10) -> list[dict]:
    """Search years of AI chat history and return source-backed candidate messages."""
    return service.search(query, min(max(limit, 1), 50))


@mcp.tool()
def memory_get_message(conversation_id: str, message_id: str) -> dict | None:
    """Return one exact canonical message, including full source content/metadata JSON and hashes."""
    return service.get_message(conversation_id, message_id)


@mcp.tool()
def memory_get_conversation(conversation_id: str, active_branch_only: bool = True) -> dict | None:
    """Return a conversation. By default reconstruct the exported active branch; optionally return all branch messages."""
    return service.get_conversation(conversation_id, active_branch_only)


@mcp.tool()
def memory_context_pack(
    query: str,
    hit_limit: int = 8,
    neighbor_depth: int = 2,
    char_budget: int = 30000,
) -> dict:
    """Build a bounded context pack of exact source messages around relevant hits."""
    return service.context_pack(
        query=query,
        hit_limit=min(max(hit_limit, 1), 30),
        neighbor_depth=min(max(neighbor_depth, 0), 5),
        char_budget=min(max(char_budget, 2000), 120000),
    )


if __name__ == "__main__":
    mcp.run(transport="streamable-http", json_response=True)
