"""Embeddings через Ollama API."""

from __future__ import annotations

import json

import httpx

from app.config import OLLAMA_BASE_URL, RAG_EMBED_MODEL


async def embed_text(text: str) -> list[float]:
    url = f"{OLLAMA_BASE_URL.rstrip('/')}/api/embeddings"
    payload = {"model": RAG_EMBED_MODEL, "prompt": text}
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
    embedding = data.get("embedding")
    if not embedding:
        raise RuntimeError(f"Ollama embeddings empty for model {RAG_EMBED_MODEL}")
    return [float(x) for x in embedding]
