"""Разбиение markdown на чанки для индексации."""

from __future__ import annotations

import re

DEFAULT_MAX_CHARS = 1200
DEFAULT_OVERLAP = 100


def chunk_markdown(text: str, source: str, max_chars: int = DEFAULT_MAX_CHARS) -> list[dict[str, str]]:
    """Возвращает список {source, heading, content}."""
    text = text.strip()
    if not text:
        return []

    sections: list[tuple[str, str]] = []
    current_heading = source
    buf: list[str] = []

    for line in text.splitlines():
        if re.match(r"^#{1,3}\s+", line):
            if buf:
                sections.append((current_heading, "\n".join(buf).strip()))
                buf = []
            current_heading = line.lstrip("#").strip() or source
        else:
            buf.append(line)
    if buf:
        sections.append((current_heading, "\n".join(buf).strip()))

    if not sections:
        sections = [(source, text)]

    chunks: list[dict[str, str]] = []
    for heading, body in sections:
        if len(body) <= max_chars:
            if body:
                chunks.append({"source": source, "heading": heading, "content": body})
            continue
        start = 0
        part = 0
        while start < len(body):
            end = min(start + max_chars, len(body))
            piece = body[start:end].strip()
            if piece:
                suffix = f" (часть {part + 1})" if part else ""
                chunks.append(
                    {
                        "source": source,
                        "heading": heading + suffix,
                        "content": piece,
                    }
                )
                part += 1
            if end >= len(body):
                break
            start = end - DEFAULT_OVERLAP

    return chunks
