"""RAG: индексация prompts/knowledge и поиск для чата виджета."""

from app.rag.ingest import reindex_knowledge_dir
from app.rag.search import build_context_message, search_chunks

__all__ = ["reindex_knowledge_dir", "search_chunks", "build_context_message"]
