# Пайплайн знаний: скрейпинг, промпт, RAG

## Обзор

| Этап | Инструмент | Результат |
|------|------------|-----------|
| Ручные факты | `prompts/knowledge/*.md` | Git, ревью |
| Скрейп (черновик) | `scripts/knowledge-scrape.sh` | `sites-scraped.md` |
| SYSTEM модели | `scripts/model-create.sh` | Ollama `truck-service` |
| RAG индекс | `scripts/knowledge-index.sh` | SQLite chunks в intake-api |
| Чат виджета | `POST /intake/api/chat` | контекст + Ollama |

## 1. Whitelist URL

Файл [scripts/knowledge-urls.txt](../scripts/knowledge-urls.txt) — только **свои** домены.

## 2. Скрейп (cron / вручную)

```bash
./scripts/knowledge-scrape.sh
# правка prompts/knowledge/sites-scraped.md
./scripts/knowledge-index.sh
./scripts/model-create.sh
```

**Cron (еженедельно):**

```cron
0 4 * * 1 cd /root/AIServer && ./scripts/knowledge-scrape.sh >> /var/log/aiserver-scrape.log 2>&1
```

После скрейпа **обязателен** ручной diff: цены, акции, мусор из меню.

## 3. n8n (опционально)

Профиль `automation` в docker-compose:

1. **Schedule** → раз в неделю  
2. **Read File** или HTTP к списку URL  
3. **HTTP Request** → каждая страница  
4. **Code** — очистка HTML (как `knowledge-scrape.py`)  
5. **Write File** на VPS → `prompts/knowledge/sites-scraped.md`  
6. **Webhook** → `POST https://agent.../intake/api/rag/reindex` (после ревью в Telegram)

## 4. Переменные окружения (intake-api / .env)

| Переменная | По умолчанию | Назначение |
|------------|--------------|------------|
| `RAG_ENABLED` | `true` | Подмешивать контекст в чат |
| `RAG_TOP_K` | `3` | Число чанков |
| `RAG_EMBED_MODEL` | `nomic-embed-text` | Модель Ollama |
| `OLLAMA_BASE_URL` | `http://ollama:11434` | API embeddings + chat |
| `KNOWLEDGE_DIR` | `/knowledge` | Mount `prompts/knowledge` |

Первый запуск embeddings:

```bash
docker exec ollama ollama pull nomic-embed-text
./scripts/knowledge-index.sh
```

## 5. RAM на 2 GB

Embedding-модель грузится по запросу; при OOM — `./scripts/model-stop.sh` между индексацией и чатом.

См. также [KNOWLEDGE-FEEDBACK.md](./KNOWLEDGE-FEEDBACK.md) — цикл по диалогам intake.
