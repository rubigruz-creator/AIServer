"""Поиск релевантных чанков по запросу пользователя."""

from __future__ import annotations

from app.config import RAG_TOP_K
from app.db import get_conn
from app.rag.embeddings import embed_text
from app.rag.store import cosine_similarity, init_rag_tables, load_all_chunks


async def search_chunks(query: str, top_k: int | None = None) -> list[dict[str, str]]:
    k = top_k if top_k is not None else RAG_TOP_K
    query = query.strip()
    if not query or k < 1:
        return []

    with get_conn() as conn:
        init_rag_tables(conn)
        stored = load_all_chunks(conn)

    if not stored:
        return []

    q_vec = await embed_text(query)
    scored: list[tuple[float, dict]] = []
    for row in stored:
        score = cosine_similarity(q_vec, row["embedding"])
        scored.append((score, row))
    scored.sort(key=lambda x: x[0], reverse=True)

    results: list[dict[str, str]] = []
    for score, row in scored[:k]:
        if score <= 0.05:
            continue
        results.append(
            {
                "source_file": row["source_file"],
                "heading": row["heading"] or "",
                "content": row["content"],
                "score": f"{score:.3f}",
            }
        )
    return results


def build_context_message(chunks: list[dict[str, str]]) -> str:
    if not chunks:
        return ""
    lines = [
        "Релевантные факты из базы знаний автосервиса (используй только их; не выдумывай цены и сроки):",
        "",
    ]
    for i, ch in enumerate(chunks, 1):
        title = ch.get("heading") or ch.get("source_file", "")
        lines.append(f"[{i}] {title}")
        lines.append(ch["content"])
        lines.append("")
    lines.append(
        "Если фактов недостаточно — скажи, что уточнит администратор. Продолжай сбор заявки по правилам."
    )
    return "\n".join(lines).strip()
