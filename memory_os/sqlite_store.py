from __future__ import annotations

import json
import sqlite3
from pathlib import Path

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS conversations (
  conversation_id TEXT PRIMARY KEY,
  title TEXT,
  create_time REAL,
  update_time REAL,
  current_node_id TEXT,
  source TEXT NOT NULL,
  source_conversation_sha256 TEXT NOT NULL,
  metadata_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS nodes (
  node_id TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  parent_node_id TEXT,
  has_message INTEGER NOT NULL,
  children_json TEXT NOT NULL,
  children_count INTEGER NOT NULL,
  is_branch_point INTEGER NOT NULL,
  is_current_node INTEGER NOT NULL,
  source TEXT NOT NULL,
  source_node_sha256 TEXT NOT NULL,
  FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
  PRIMARY KEY (conversation_id, node_id)
);

CREATE TABLE IF NOT EXISTS messages (
  message_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  conversation_id TEXT NOT NULL,
  parent_node_id TEXT,
  role TEXT,
  author_name TEXT,
  create_time REAL,
  update_time REAL,
  status TEXT,
  recipient TEXT,
  weight REAL,
  end_turn INTEGER,
  content_type TEXT,
  text TEXT NOT NULL,
  text_sha256 TEXT NOT NULL,
  content_json TEXT NOT NULL,
  metadata_json TEXT NOT NULL,
  message_json TEXT NOT NULL,
  source TEXT NOT NULL,
  source_message_sha256 TEXT NOT NULL,
  FOREIGN KEY (conversation_id) REFERENCES conversations(conversation_id),
  FOREIGN KEY (conversation_id, node_id) REFERENCES nodes(conversation_id, node_id),
  PRIMARY KEY (conversation_id, message_id)
);

CREATE TABLE IF NOT EXISTS edges (
  conversation_id TEXT NOT NULL,
  parent_node_id TEXT NOT NULL,
  child_node_id TEXT NOT NULL,
  edge_type TEXT NOT NULL,
  source TEXT NOT NULL,
  PRIMARY KEY (conversation_id, parent_node_id, child_node_id)
);

CREATE TABLE IF NOT EXISTS attachments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id TEXT NOT NULL,
  message_id TEXT NOT NULL,
  node_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  ref TEXT NOT NULL,
  metadata_json TEXT,
  source TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, create_time);
CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
CREATE INDEX IF NOT EXISTS idx_nodes_conversation ON nodes(conversation_id);
CREATE INDEX IF NOT EXISTS idx_attachments_message ON attachments(message_id);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
  message_id UNINDEXED,
  conversation_id UNINDEXED,
  role UNINDEXED,
  text,
  tokenize='unicode61'
);
"""


def _rows(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def build_sqlite(canonical_dir: Path, db_path: Path) -> None:
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.execute("BEGIN")
        for r in _rows(canonical_dir / "conversations.jsonl"):
            conn.execute("INSERT INTO conversations VALUES (?,?,?,?,?,?,?,?)", (
                r["conversation_id"], r["title"], r["create_time"], r["update_time"], r["current_node_id"],
                r["source"], r["source_conversation_sha256"], r["metadata_json"]
            ))
        for r in _rows(canonical_dir / "nodes.jsonl"):
            conn.execute("INSERT INTO nodes VALUES (?,?,?,?,?,?,?,?,?,?)", (
                r["node_id"], r["conversation_id"], r["parent_node_id"], int(r["has_message"]),
                json.dumps(r["children"], ensure_ascii=False), r["children_count"], int(r["is_branch_point"]),
                int(r["is_current_node"]), r["source"], r["source_node_sha256"]
            ))
        for r in _rows(canonical_dir / "edges.jsonl"):
            conn.execute("INSERT INTO edges VALUES (?,?,?,?,?)", (
                r["conversation_id"], r["parent_node_id"], r["child_node_id"], r["edge_type"], r["source"]
            ))
        for r in _rows(canonical_dir / "messages.jsonl"):
            conn.execute("INSERT INTO messages VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                r["message_id"], r["node_id"], r["conversation_id"], r["parent_node_id"], r["role"], r["author_name"],
                r["create_time"], r["update_time"], r["status"], r["recipient"], r["weight"],
                None if r["end_turn"] is None else int(bool(r["end_turn"])), r["content_type"], r["text"], r["text_sha256"],
                r["content_json"], r["metadata_json"], r["message_json"], r["source"], r["source_message_sha256"]
            ))
            conn.execute("INSERT INTO messages_fts(message_id,conversation_id,role,text) VALUES (?,?,?,?)", (
                r["message_id"], r["conversation_id"], r["role"], r["text"]
            ))
        for r in _rows(canonical_dir / "attachments.jsonl"):
            conn.execute("INSERT INTO attachments(conversation_id,message_id,node_id,kind,ref,metadata_json,source) VALUES (?,?,?,?,?,?,?)", (
                r["conversation_id"], r["message_id"], r["node_id"], r["kind"], r["ref"], r["metadata_json"], r["source"]
            ))
        conn.commit()
        conn.execute("PRAGMA optimize")
    finally:
        conn.close()
