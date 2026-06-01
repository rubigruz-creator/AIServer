import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import DB_PATH


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_db() -> None:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                source_url TEXT,
                user_agent TEXT,
                has_application INTEGER NOT NULL DEFAULT 0,
                application_at TEXT,
                application_line TEXT,
                client_name TEXT,
                client_phone TEXT,
                vehicle TEXT,
                service_type TEXT,
                visit_time TEXT
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id)
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON messages(conversation_id, created_at);
            CREATE INDEX IF NOT EXISTS idx_conversations_created
                ON conversations(created_at DESC);
            """
        )
        from app.rag.store import init_rag_tables

        init_rag_tables(conn)


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def delete_conversation(conn: sqlite3.Connection, conversation_id: str) -> bool:
    cur = conn.execute("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
    if not cur.fetchone():
        return False
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    return True


def purge_conversations_below_message_count(
    conn: sqlite3.Connection, min_messages: int
) -> int:
    """Удаляет диалоги, у которых строго меньше min_messages сообщений."""
    if min_messages < 1:
        return 0
    rows = conn.execute(
        """
        SELECT c.id
        FROM conversations c
        LEFT JOIN (
            SELECT conversation_id, COUNT(*) AS cnt
            FROM messages
            GROUP BY conversation_id
        ) m ON m.conversation_id = c.id
        WHERE COALESCE(m.cnt, 0) < ?
        """,
        (min_messages,),
    ).fetchall()
    deleted = 0
    for row in rows:
        if delete_conversation(conn, row["id"]):
            deleted += 1
    return deleted
