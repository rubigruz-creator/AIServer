"""SQLite-хранилище чанков и векторов."""

from __future__ import annotations

import json
import math
import sqlite3
from typing import Any

from app.db import get_conn, utc_now_iso


def init_rag_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS knowledge_chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,
            heading TEXT,
            content TEXT NOT NULL,
            embedding_json TEXT NOT NULL,
            indexed_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_knowledge_source
            ON knowledge_chunks(source_file);
        """
    )


def clear_chunks(conn: sqlite3.Connection) -> None:
    conn.execute("DELETE FROM knowledge_chunks")


def insert_chunk(
    conn: sqlite3.Connection,
    source_file: str,
    heading: str,
    content: str,
    embedding: list[float],
) -> None:
    conn.execute(
        """
        INSERT INTO knowledge_chunks (source_file, heading, content, embedding_json, indexed_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (source_file, heading, content, json.dumps(embedding), utc_now_iso()),
    )


def load_all_chunks(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, source_file, heading, content, embedding_json FROM knowledge_chunks"
    ).fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "id": row["id"],
                "source_file": row["source_file"],
                "heading": row["heading"],
                "content": row["content"],
                "embedding": json.loads(row["embedding_json"]),
            }
        )
    return out


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
