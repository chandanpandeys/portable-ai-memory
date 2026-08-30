"""Vercel/ASGI REST + MCP gateway.

The private database and MEMORY_CAPABILITY_TOKEN must be supplied at deploy time.
Do not commit either one.
"""
from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from mcp.server import MCPServer

from memory_os.service import MemoryService

DB_PATH = Path(os.environ.get("MEMORY_DB_PATH", "/tmp/memory.sqlite"))
TOKEN = os.environ.get("MEMORY_CAPABILITY_TOKEN", "").strip()
if not TOKEN:
    raise RuntimeError("MEMORY_CAPABILITY_TOKEN is required")

service = MemoryService(DB_PATH)
mcp = MCPServer("Portable AI Memory")


@mcp.tool()
def memory_stats() -> dict[str, int]:
    return service.stats()


@mcp.tool()
def memory_search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    return service.search(query, min(max(limit, 1), 50))


@mcp.tool()
def memory_get_message(conversation_id: str, message_id: str) -> dict[str, Any] | None:
    return service.get_message(conversation_id, message_id)


@mcp.tool()
def memory_get_conversation(conversation_id: str, active_branch_only: bool = True) -> dict[str, Any] | None:
    return service.get_conversation(conversation_id, active_branch_only)


@mcp.tool()
def memory_context_pack(query: str, hit_limit: int = 8, neighbor_depth: int = 2, char_budget: int = 30000) -> dict[str, Any]:
    return service.context_pack(query, hit_limit, neighbor_depth, char_budget)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    async with mcp.session_manager.run():
        yield


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)


@app.middleware("http")
async def privacy_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store, private"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


PREFIX = f"/api/{TOKEN}"


@app.get(f"{PREFIX}/stats")
def stats():
    return service.stats()


@app.get(f"{PREFIX}/search")
def search(q: str = Query(min_length=1, max_length=2000), limit: int = 10):
    return service.search(q, min(max(limit, 1), 50))


@app.get(f"{PREFIX}/message")
def message(conversation_id: str, message_id: str):
    result = service.get_message(conversation_id, message_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Message not found")
    return result


@app.get(f"{PREFIX}/conversation")
def conversation(conversation_id: str, active_branch_only: bool = True):
    result = service.get_conversation(conversation_id, active_branch_only)
    if result is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return result


@app.get(f"{PREFIX}/context")
def context(q: str, hit_limit: int = 8, neighbor_depth: int = 2, char_budget: int = 30000):
    return service.context_pack(q, hit_limit, neighbor_depth, char_budget)


mcp_app = mcp.streamable_http_app(streamable_http_path="/", stateless_http=True, json_response=True)
app.mount(f"/mcp/{TOKEN}", mcp_app)
