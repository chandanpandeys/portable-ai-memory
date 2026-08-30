from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from .context_pack import build_context_pack, search_hits


class MemoryService:
    """Read-only facade over canonical Memory OS data."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(self.db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def stats(self) -> dict[str, int]:
        conn = self._connect()
        try:
            return {
                "conversations": conn.execute("SELECT count(*) FROM conversations").fetchone()[0],
                "nodes": conn.execute("SELECT count(*) FROM nodes").fetchone()[0],
                "messages": conn.execute("SELECT count(*) FROM messages").fetchone()[0],
                "edges": conn.execute("SELECT count(*) FROM edges").fetchone()[0],
                "attachments": conn.execute("SELECT count(*) FROM attachments").fetchone()[0],
                "branch_points": conn.execute("SELECT count(*) FROM nodes WHERE is_branch_point=1").fetchone()[0],
            }
        finally:
            conn.close()

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            rows = search_hits(conn, query, limit)
            return [{
                "conversation_id": r["conversation_id"],
                "message_id": r["message_id"],
                "node_id": r["node_id"],
                "title": r["title"],
                "role": r["role"],
                "create_time": r["create_time"],
                "score": r["score"],
                "preview": (r["text"] or "")[:1200],
            } for r in rows]
        finally:
            conn.close()

    def get_message(self, conversation_id: str, message_id: str) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            row = conn.execute(
                """SELECT m.*, c.title FROM messages m
                   JOIN conversations c ON c.conversation_id=m.conversation_id
                   WHERE m.conversation_id=? AND m.message_id=?""",
                (conversation_id, message_id),
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_conversation(self, conversation_id: str, active_branch_only: bool = True) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            conv = conn.execute("SELECT * FROM conversations WHERE conversation_id=?", (conversation_id,)).fetchone()
            if not conv:
                return None
            if not active_branch_only:
                messages = [dict(r) for r in conn.execute(
                    "SELECT * FROM messages WHERE conversation_id=? ORDER BY coalesce(create_time,0), node_id",
                    (conversation_id,),
                )]
                return {"conversation": dict(conv), "messages": messages, "mode": "all_messages"}

            current = conv["current_node_id"]
            path: list[str] = []
            seen: set[str] = set()
            while current and current not in seen:
                seen.add(current)
                path.append(current)
                row = conn.execute(
                    "SELECT parent_node_id FROM nodes WHERE conversation_id=? AND node_id=?",
                    (conversation_id, current),
                ).fetchone()
                current = row[0] if row else None
            path.reverse()
            messages = []
            for node_id in path:
                row = conn.execute(
                    "SELECT * FROM messages WHERE conversation_id=? AND node_id=?",
                    (conversation_id, node_id),
                ).fetchone()
                if row:
                    messages.append(dict(row))
            return {"conversation": dict(conv), "messages": messages, "mode": "active_branch"}
        finally:
            conn.close()

    def context_pack(self, query: str, hit_limit: int = 8, neighbor_depth: int = 2, char_budget: int = 30000) -> dict[str, Any]:
        return build_context_pack(self.db_path, query, hit_limit, neighbor_depth, char_budget)
