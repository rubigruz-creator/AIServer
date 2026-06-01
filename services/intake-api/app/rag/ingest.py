"""Индексация markdown из KNOWLEDGE_DIR."""

from __future__ import annotations

from pathlib import Path

from app.config import KNOWLEDGE_DIR, RAG_INDEX_DRAFTS
from app.db import get_conn
from app.rag.chunking import chunk_markdown
from app.rag.embeddings import embed_text
from app.rag.store import clear_chunks, init_rag_tables, insert_chunk


async def reindex_knowledge_dir(knowledge_dir: Path | None = None) -> dict[str, int]:
    base = knowledge_dir or KNOWLEDGE_DIR
    if not base.is_dir():
        raise FileNotFoundError(f"KNOWLEDGE_DIR not found: {base}")

    files = sorted(
        p
        for p in base.glob("*.md")
        if p.is_file()
        and p.name.lower() != "readme.md"
        and (RAG_INDEX_DRAFTS or p.name != "sites-scraped.md")
    )
    chunks_total = 0
    files_indexed = 0

    with get_conn() as conn:
        init_rag_tables(conn)
        clear_chunks(conn)

        for path in files:
            text = path.read_text(encoding="utf-8")
            chunks = chunk_markdown(text, source=path.name)
            if not chunks:
                continue
            files_indexed += 1
            for ch in chunks:
                body = f"{ch['heading']}\n\n{ch['content']}" if ch["heading"] else ch["content"]
                vec = await embed_text(body)
                insert_chunk(conn, path.name, ch["heading"], ch["content"], vec)
                chunks_total += 1

    return {"files": files_indexed, "chunks": chunks_total}
