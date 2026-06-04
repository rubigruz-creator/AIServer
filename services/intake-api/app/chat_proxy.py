"""Прокси чата Ollama с подмешиванием RAG-контекста."""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

import httpx

logger = logging.getLogger(__name__)
from fastapi import Request
from fastapi.responses import StreamingResponse

from app.config import CHAT_MODEL, OLLAMA_BASE_URL, RAG_ENABLED
from app.rag.search import build_context_message, search_chunks

OLLAMA_CHAT_URL = f"{OLLAMA_BASE_URL.rstrip('/')}/api/chat"


def _last_user_message(messages: list[dict[str, Any]]) -> str:
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
    return ""


async def _inject_rag(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not RAG_ENABLED:
        return messages
    query = _last_user_message(messages)
    if not query:
        return messages
    try:
        chunks = await search_chunks(query)
    except Exception as exc:
        logger.warning("RAG search failed, chat without knowledge context: %s", exc)
        return messages
    context = build_context_message(chunks)
    if not context:
        logger.info("RAG: no chunks for query=%r (index empty or low score?)", query[:80])
        return messages
    logger.debug("RAG: %d chunks for query=%r", len(chunks), query[:80])
    rag_msg = {"role": "system", "content": context}
    out = list(messages)
    last_user_idx = -1
    for i, msg in enumerate(messages):
        if msg.get("role") == "user":
            last_user_idx = i
    if last_user_idx >= 0:
        out.insert(last_user_idx, rag_msg)
    else:
        out.insert(0, rag_msg)
    return out


async def _stream_ollama(body: dict[str, Any]) -> AsyncIterator[bytes]:
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", OLLAMA_CHAT_URL, json=body) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_bytes():
                yield chunk


async def proxy_chat(request: Request) -> StreamingResponse:
    raw = await request.body()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="invalid json") from exc

    if not payload.get("model"):
        payload["model"] = CHAT_MODEL

    messages = payload.get("messages")
    if isinstance(messages, list):
        payload["messages"] = await _inject_rag(messages)

    stream = payload.get("stream", True)

    if stream:

        async def generate() -> AsyncIterator[bytes]:
            async for chunk in _stream_ollama(payload):
                yield chunk

        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
        )

    from fastapi.responses import Response

    async with httpx.AsyncClient(timeout=300.0) as client:
        resp = await client.post(OLLAMA_CHAT_URL, json=payload)
        resp.raise_for_status()
        return Response(content=resp.content, media_type="application/json")
