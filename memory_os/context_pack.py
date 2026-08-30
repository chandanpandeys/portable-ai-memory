from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import defaultdict, deque
from pathlib import Path
from typing import Any


def fts_query_from_text(query: str) -> str:
    """Turn a natural-language query into a tolerant FTS5 OR query."""
    tokens = re.findall(r"[\w][\w.+#/-]{1,}", query, flags=re.UNICODE)
    # Deduplicate while preserving order and avoid common filler terms.
    stop = {"the","a","an","and","or","of","to","in","for","on","is","was","i","my","we","about","what","did"}
    cleaned = []
    seen = set()
    for token in tokens:
        key = token.casefold()
        if key in stop or key in seen:
            continue
        seen.add(key)
        # Quote tokens because punctuation such as C++ has FTS syntax meaning.
        cleaned.append('"' + token.replace('"', '""') + '"')
    return " OR ".join(cleaned[:24]) or '""'


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def search_hits(conn: sqlite3.Connection, query: str, limit: int = 10) -> list[dict[str, Any]]:
    fts = fts_query_from_text(query)
    sql = """
    SELECT m.message_id, m.node_id, m.conversation_id, m.parent_node_id, m.role,
           m.create_time, m.text, c.title, bm25(messages_fts) AS score
    FROM messages_fts
    JOIN messages m ON m.message_id = messages_fts.message_id
      AND m.conversation_id = messages_fts.conversation_id
    JOIN conversations c ON c.conversation_id = m.conversation_id
    WHERE messages_fts MATCH ?
    ORDER BY score
    LIMIT ?
    """
    return [dict(r) for r in conn.execute(sql, (fts, limit))]


def _message_for_node(conn: sqlite3.Connection, conversation_id: str, node_id: str):
    return conn.execute(
        "SELECT * FROM messages WHERE conversation_id=? AND node_id=?",
        (conversation_id, node_id),
    ).fetchone()


def expand_neighbors(conn: sqlite3.Connection, conversation_id: str, start_node: str, depth: int = 2) -> list[dict[str, Any]]:
    """Expand parent/child graph around a hit without flattening branches."""
    q = deque([(start_node, 0)])
    visited = {start_node}
    node_distance = {start_node: 0}
    while q:
        node_id, dist = q.popleft()
        if dist >= depth:
            continue
        parent = conn.execute(
            "SELECT parent_node_id FROM nodes WHERE conversation_id=? AND node_id=?",
            (conversation_id, node_id),
        ).fetchone()
        candidates: list[str] = []
        if parent and parent[0]:
            candidates.append(parent[0])
        candidates += [r[0] for r in conn.execute(
            "SELECT child_node_id FROM edges WHERE conversation_id=? AND parent_node_id=?",
            (conversation_id, node_id),
        )]
        for nxt in candidates:
            if nxt not in visited:
                visited.add(nxt)
                node_distance[nxt] = dist + 1
                q.append((nxt, dist + 1))

    rows = []
    for node_id, dist in sorted(node_distance.items(), key=lambda x: (x[1], x[0])):
        msg = _message_for_node(conn, conversation_id, node_id)
        if msg:
            rows.append({
                "message_id": msg["message_id"],
                "node_id": node_id,
                "conversation_id": conversation_id,
                "role": msg["role"],
                "create_time": msg["create_time"],
                "text": msg["text"],
                "distance": dist,
            })
    return rows


def build_context_pack(db_path: Path, query: str, hit_limit: int = 8, neighbor_depth: int = 2, char_budget: int = 30000) -> dict[str, Any]:
    conn = _connect(db_path)
    try:
        hits = search_hits(conn, query, hit_limit)
        conversations: dict[str, dict[str, Any]] = {}
        total_chars = 0
        included_message_keys: set[tuple[str, str]] = set()

        for hit in hits:
            cid = hit["conversation_id"]
            bucket = conversations.setdefault(cid, {
                "conversation_id": cid,
                "title": hit["title"],
                "best_score": hit["score"],
                "hit_message_ids": [],
                "messages": [],
            })
            bucket["best_score"] = min(bucket["best_score"], hit["score"])
            bucket["hit_message_ids"].append(hit["message_id"])
            for msg in expand_neighbors(conn, cid, hit["node_id"], neighbor_depth):
                key = (cid, msg["message_id"])
                if key in included_message_keys:
                    continue
                text = msg["text"] or ""
                if total_chars + len(text) > char_budget and total_chars > 0:
                    continue
                included_message_keys.add(key)
                bucket["messages"].append(msg)
                total_chars += len(text)

        ordered = sorted(conversations.values(), key=lambda c: c["best_score"])
        for conv in ordered:
            conv["messages"].sort(key=lambda m: ((m["create_time"] is None), m["create_time"] or 0, m["distance"]))
        return {
            "query": query,
            "retrieval": {
                "method": "sqlite_fts5_plus_message_graph_neighbors",
                "hit_limit": hit_limit,
                "neighbor_depth": neighbor_depth,
                "char_budget": char_budget,
                "included_characters": total_chars,
            },
            "conversations": ordered,
            "provenance_rule": "Every excerpt is exact canonical message text and includes its conversation_id and message_id.",
        }
    finally:
        conn.close()


def to_markdown(pack: dict[str, Any]) -> str:
    out = [f"# Memory Context Pack", "", f"Query: {pack['query']}", ""]
    for conv in pack["conversations"]:
        out += [f"## {conv['title'] or '(untitled)'}", f"Conversation ID: `{conv['conversation_id']}`", ""]
        hit_ids = set(conv["hit_message_ids"])
        for msg in conv["messages"]:
            marker = " [SEARCH HIT]" if msg["message_id"] in hit_ids else ""
            out += [f"### {msg['role']}{marker}", f"Message ID: `{msg['message_id']}`", "", msg["text"], ""]
    out += ["---", pack["provenance_rule"]]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a source-backed context pack from Memory OS")
    parser.add_argument("db", type=Path)
    parser.add_argument("query")
    parser.add_argument("--hits", type=int, default=8)
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--chars", type=int, default=30000)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()
    pack = build_context_pack(args.db, args.query, args.hits, args.depth, args.chars)
    print(json.dumps(pack, ensure_ascii=False, indent=2) if args.format == "json" else to_markdown(pack))


if __name__ == "__main__":
    main()
