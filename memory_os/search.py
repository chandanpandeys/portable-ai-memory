from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def search(db_path: Path, query: str, limit: int = 10):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        sql = """
        SELECT m.message_id, m.conversation_id, m.role, m.create_time, c.title,
               snippet(messages_fts, 3, '[', ']', ' … ', 24) AS snippet,
               bm25(messages_fts) AS score
        FROM messages_fts
        JOIN messages m ON m.message_id = messages_fts.message_id AND m.conversation_id = messages_fts.conversation_id
        JOIN conversations c ON c.conversation_id = m.conversation_id
        WHERE messages_fts MATCH ?
        ORDER BY score
        LIMIT ?
        """
        return [dict(row) for row in conn.execute(sql, (query, limit))]
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Search canonical Memory OS SQLite store")
    parser.add_argument("db", type=Path)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    for row in search(args.db, args.query, args.limit):
        print(f"{row['score']:.3f}\t{row['title']}\t{row['role']}\t{row['message_id']}\n  {row['snippet']}\n")


if __name__ == "__main__":
    main()
