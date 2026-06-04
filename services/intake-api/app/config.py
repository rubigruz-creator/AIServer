import os
from pathlib import Path

DB_PATH = os.getenv("INTAKE_DB_PATH", "/data/intake.db")
ADMIN_USER = os.getenv("INTAKE_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("INTAKE_ADMIN_PASSWORD", "")
WEBHOOK_URL = os.getenv("INTAKE_WEBHOOK_URL", "").strip()
TZ = os.getenv("TZ", "Europe/Moscow")
# При старте удалять диалоги с числом сообщений < N (0 = отключить)
AUTO_PURGE_MIN_MESSAGES = int(os.getenv("INTAKE_AUTO_PURGE_MIN_MESSAGES", "3"))

# RAG + прокси чата Ollama
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434").rstrip("/")
CHAT_MODEL = os.getenv("CHAT_MODEL", "truck-service:latest")
OLLAMA_KEEP_ALIVE = os.getenv("OLLAMA_KEEP_ALIVE", "-1")
CHAT_DEFAULT_NUM_PREDICT = int(os.getenv("CHAT_DEFAULT_NUM_PREDICT", "384"))
RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() in ("1", "true", "yes")
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "3"))
RAG_EMBED_MODEL = os.getenv("RAG_EMBED_MODEL", "nomic-embed-text")
# false = только keyword-поиск (быстро, без загрузки nomic-embed-text на каждый чат)
RAG_USE_EMBEDDINGS = os.getenv("RAG_USE_EMBEDDINGS", "false").lower() in (
    "1",
    "true",
    "yes",
)
KNOWLEDGE_DIR = Path(os.getenv("KNOWLEDGE_DIR", "/knowledge"))
# Индексировать sites-scraped.md только после ручной проверки
RAG_INDEX_DRAFTS = os.getenv("RAG_INDEX_DRAFTS", "false").lower() in ("1", "true", "yes")
