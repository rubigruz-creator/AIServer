"""Поиск релевантных чанков: embeddings + ключевые слова (для коротких запросов на русском)."""

from __future__ import annotations

import re

from app.config import RAG_TOP_K
from app.db import get_conn
from app.rag.embeddings import embed_text
from app.rag.store import cosine_similarity, init_rag_tables, load_all_chunks

# Запросы про эти темы — всегда подмешивать чанк «Что не делаем», если он есть в индексе
_NEGATIVE_TRIGGERS = (
    "кузов",
    "кузовн",
    "развал",
    "схожден",
    "автомой",
    "мойк",
    "выезд",
    "на выезд",
    "к вам на",
)


def _tokenize(text: str) -> list[str]:
    return [w for w in re.findall(r"[а-яёa-z0-9]{3,}", text.lower()) if len(w) >= 3]


def _keyword_score(query: str, content: str) -> float:
    words = _tokenize(query)
    if not words:
        return 0.0
    blob = content.lower()
    hits = sum(1 for w in words if w in blob)
    return hits / len(words)


def _needs_negative_chunk(query: str) -> bool:
    q = query.lower()
    return any(t in q for t in _NEGATIVE_TRIGGERS)


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

    scored: list[tuple[float, dict]] = []
    try:
        q_vec = await embed_text(query)
        for row in stored:
            cos = cosine_similarity(q_vec, row["embedding"])
            kw = _keyword_score(query, row["content"] + " " + (row.get("heading") or ""))
            combined = 0.55 * cos + 0.45 * kw
            scored.append((combined, row))
    except Exception:
        for row in stored:
            kw = _keyword_score(query, row["content"] + " " + (row.get("heading") or ""))
            scored.append((kw, row))

    scored.sort(key=lambda x: x[0], reverse=True)

    seen_ids: set[int] = set()
    results: list[dict[str, str]] = []

    def append_row(score: float, row: dict) -> None:
        rid = row["id"]
        if rid in seen_ids:
            return
        if score <= 0.02 and not _needs_negative_chunk(query):
            return
        seen_ids.add(rid)
        results.append(
            {
                "source_file": row["source_file"],
                "heading": row["heading"] or "",
                "content": row["content"],
                "score": f"{score:.3f}",
            }
        )

    if _needs_negative_chunk(query):
        for row in stored:
            heading = (row.get("heading") or "").lower()
            body = row["content"].lower()
            if "не делаем" in heading or "не делаем" in body[:80]:
                append_row(1.0, row)
                break

    for score, row in scored:
        if len(results) >= k:
            break
        append_row(score, row)

    return results[:k]


def build_context_message(chunks: list[dict[str, str]]) -> str:
    if not chunks:
        return ""
    lines = [
        "Релевантные факты из базы знаний автосервиса.",
        "ОБЯЗАТЕЛЬНО следуй им. Если написано «не делаем» / «не выполняем» — ответ «Нет».",
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
