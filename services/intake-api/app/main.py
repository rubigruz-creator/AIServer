import asyncio
import secrets
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

from app import applications as app_parser
from app.config import (
    ADMIN_PASSWORD,
    ADMIN_USER,
    AUTO_PURGE_MIN_MESSAGES,
    KNOWLEDGE_DIR,
    RAG_EMBED_MODEL,
    RAG_ENABLED,
    RAG_USE_EMBEDDINGS,
)
from app.db import (
    delete_conversation,
    get_conn,
    init_db,
    purge_conversations_below_message_count,
    row_to_dict,
    utc_now_iso,
)

SORT_FIELDS = {
    "created_at": "c.created_at",
    "updated_at": "c.updated_at",
    "message_count": "message_count",
    "has_application": "c.has_application",
    "client_phone": "c.client_phone",
    "vehicle": "c.vehicle",
    "service_type": "c.service_type",
    "source_url": "c.source_url",
}
from app.notifications import notify_application_created
from app.chat_proxy import proxy_chat, warmup_chat_model
from app.rag.ingest import reindex_knowledge_dir

app = FastAPI(title="AIServer Intake API", version="1.1.0")
security = HTTPBasic()
STATIC_DIR = Path(__file__).parent / "static"


class SessionCreate(BaseModel):
    session_id: str | None = None
    source_url: str | None = None
    user_agent: str | None = None


class MessageCreate(BaseModel):
    session_id: str = Field(min_length=8, max_length=64)
    role: str = Field(pattern="^(user|assistant|system)$")
    content: str = Field(min_length=0, max_length=32000)


def require_admin(credentials: Annotated[HTTPBasicCredentials, Depends(security)]) -> str:
    if not ADMIN_PASSWORD:
        raise HTTPException(
            status_code=503,
            detail="INTAKE_ADMIN_PASSWORD не задан на сервере",
        )
    user_ok = secrets.compare_digest(credentials.username, ADMIN_USER)
    pass_ok = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (user_ok and pass_ok):
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@app.on_event("startup")
async def on_startup() -> None:
    init_db()
    if AUTO_PURGE_MIN_MESSAGES > 0:
        with get_conn() as conn:
            purge_conversations_below_message_count(conn, AUTO_PURGE_MIN_MESSAGES)
    asyncio.create_task(warmup_chat_model())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/chat")
async def chat_with_rag(request: Request) -> Any:
    """Прокси Ollama /api/chat с RAG-контекстом (виджет)."""
    return await proxy_chat(request)


@app.get("/api/rag/status")
def rag_status(_user: Annotated[str, Depends(require_admin)]) -> dict[str, Any]:
    """Сколько чанков в индексе, включён ли RAG (для проверки синхронизации)."""
    from app.rag.store import init_rag_tables, load_all_chunks

    with get_conn() as conn:
        init_rag_tables(conn)
        chunks = load_all_chunks(conn)
    sources: dict[str, int] = {}
    for ch in chunks:
        sf = ch.get("source_file", "?")
        sources[sf] = sources.get(sf, 0) + 1
    knowledge_files = []
    if KNOWLEDGE_DIR.is_dir():
        knowledge_files = sorted(
            p.name for p in KNOWLEDGE_DIR.glob("*.md") if p.name.lower() != "readme.md"
        )
    return {
        "rag_enabled": RAG_ENABLED,
        "rag_use_embeddings": RAG_USE_EMBEDDINGS,
        "embed_model": RAG_EMBED_MODEL,
        "knowledge_dir": str(KNOWLEDGE_DIR),
        "knowledge_files_on_disk": knowledge_files,
        "chunks_indexed": len(chunks),
        "chunks_by_source": sources,
    }


@app.post("/api/rag/reindex")
async def rag_reindex(_user: Annotated[str, Depends(require_admin)]) -> dict[str, Any]:
    """Переиндексация prompts/knowledge → векторное хранилище."""
    try:
        stats = await reindex_knowledge_dir()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"reindex failed: {exc}") from exc
    return {"ok": True, **stats}


@app.post("/api/session")
def create_or_touch_session(body: SessionCreate, request: Request) -> dict[str, str]:
    session_id = (body.session_id or "").strip() or str(uuid.uuid4())
    now = utc_now_iso()
    source = body.source_url or request.headers.get("referer")
    ua = body.user_agent or request.headers.get("user-agent")

    with get_conn() as conn:
        existing = conn.execute(
            "SELECT id FROM conversations WHERE id = ?", (session_id,)
        ).fetchone()
        if existing:
            conn.execute(
                """
                UPDATE conversations
                SET updated_at = ?, source_url = COALESCE(?, source_url),
                    user_agent = COALESCE(?, user_agent)
                WHERE id = ?
                """,
                (now, source, ua, session_id),
            )
        else:
            conn.execute(
                """
                INSERT INTO conversations (
                    id, created_at, updated_at, source_url, user_agent
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, now, now, source, ua),
            )
    return {"session_id": session_id}


@app.post("/api/messages")
async def append_message(body: MessageCreate) -> dict[str, Any]:
    now = utc_now_iso()
    application_payload: dict[str, Any] | None = None

    with get_conn() as conn:
        row = conn.execute(
            "SELECT id, has_application FROM conversations WHERE id = ?",
            (body.session_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="session not found")

        conn.execute(
            """
            INSERT INTO messages (conversation_id, role, content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (body.session_id, body.role, body.content, now),
        )
        conn.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?",
            (now, body.session_id),
        )

        if body.role == "assistant" and not row["has_application"]:
            parsed = app_parser.parse_application_line(body.content)
            if parsed:
                conn.execute(
                    """
                    UPDATE conversations SET
                        has_application = 1,
                        application_at = ?,
                        application_line = ?,
                        client_name = ?,
                        client_phone = ?,
                        vehicle = ?,
                        service_type = ?,
                        visit_time = ?
                    WHERE id = ?
                    """,
                    (
                        now,
                        parsed.get("application_line"),
                        parsed.get("client_name"),
                        parsed.get("client_phone"),
                        parsed.get("vehicle"),
                        parsed.get("service_type"),
                        parsed.get("visit_time"),
                        body.session_id,
                    ),
                )
                application_payload = {
                    "event": "application_created",
                    "conversation_id": body.session_id,
                    "created_at": now,
                    **parsed,
                }

    if application_payload:
        await notify_application_created(application_payload)

    return {"ok": True, "application_detected": application_payload is not None}


@app.get("/admin", response_class=HTMLResponse)
def admin_page(_user: Annotated[str, Depends(require_admin)]) -> FileResponse:
    return FileResponse(STATIC_DIR / "admin.html")


@app.get("/api/admin/conversations")
def list_conversations(
    _user: Annotated[str, Depends(require_admin)],
    limit: int = 100,
    offset: int = 0,
    applications_only: bool = False,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> dict[str, Any]:
    limit = min(max(limit, 1), 500)
    offset = max(offset, 0)
    order_col = SORT_FIELDS.get(sort_by, SORT_FIELDS["created_at"])
    order_dir = "ASC" if sort_order.lower() == "asc" else "DESC"
    where = "WHERE c.has_application = 1" if applications_only else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT c.*,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) AS message_count
            FROM conversations c
            {where}
            ORDER BY {order_col} {order_dir}, c.id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        total = conn.execute(
            f"SELECT COUNT(*) AS n FROM conversations c {where}"
        ).fetchone()["n"]
    return {
        "total": total,
        "items": [row_to_dict(r) for r in rows],
        "sort_by": sort_by if sort_by in SORT_FIELDS else "created_at",
        "sort_order": order_dir.lower(),
    }


@app.delete("/api/admin/conversations/{conversation_id}")
def delete_conversation_admin(
    conversation_id: str,
    _user: Annotated[str, Depends(require_admin)],
) -> dict[str, Any]:
    with get_conn() as conn:
        if not delete_conversation(conn, conversation_id):
            raise HTTPException(status_code=404, detail="not found")
    return {"ok": True, "deleted_id": conversation_id}


@app.post("/api/admin/purge-short")
def purge_short_conversations(
    _user: Annotated[str, Depends(require_admin)],
    min_messages: int = 3,
) -> dict[str, Any]:
    min_messages = max(min_messages, 1)
    with get_conn() as conn:
        deleted = purge_conversations_below_message_count(conn, min_messages)
    return {"ok": True, "deleted_count": deleted, "min_messages": min_messages}


@app.get("/api/admin/feedback-report")
def feedback_report(
    _user: Annotated[str, Depends(require_admin)],
    limit: int = 200,
    min_user_messages: int = 2,
) -> dict[str, Any]:
    """
    Черновик для ежемесячного разбора: диалоги без заявки с несколькими вопросами клиента.
    Добавляйте вывод в prompts/knowledge/faq.md после ревью.
    """
    limit = min(max(limit, 1), 500)
    min_user_messages = max(min_user_messages, 1)
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT c.id, c.source_url, c.updated_at, c.has_application,
                   (SELECT COUNT(*) FROM messages m
                    WHERE m.conversation_id = c.id AND m.role = 'user') AS user_msgs
            FROM conversations c
            WHERE c.has_application = 0
            ORDER BY c.updated_at DESC
            LIMIT ?
            """,
            (limit * 3,),
        ).fetchall()
        items: list[dict[str, Any]] = []
        for row in rows:
            if row["user_msgs"] < min_user_messages:
                continue
            msgs = conn.execute(
                """
                SELECT role, content, created_at FROM messages
                WHERE conversation_id = ? AND role IN ('user', 'assistant')
                ORDER BY created_at ASC, id ASC
                """,
                (row["id"],),
            ).fetchall()
            items.append(
                {
                    "conversation_id": row["id"],
                    "source_url": row["source_url"],
                    "updated_at": row["updated_at"],
                    "user_messages": row["user_msgs"],
                    "messages": [row_to_dict(m) for m in msgs],
                }
            )
            if len(items) >= limit:
                break
    return {
        "total": len(items),
        "hint": "Перенесите частые вопросы в prompts/knowledge/faq.md, затем knowledge-index + model-create",
        "items": items,
    }


@app.get("/api/admin/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    _user: Annotated[str, Depends(require_admin)],
) -> dict[str, Any]:
    with get_conn() as conn:
        conv = conn.execute(
            "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
        ).fetchone()
        if not conv:
            raise HTTPException(status_code=404, detail="not found")
        messages = conn.execute(
            """
            SELECT id, role, content, created_at
            FROM messages WHERE conversation_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (conversation_id,),
        ).fetchall()
    return {
        "conversation": row_to_dict(conv),
        "messages": [row_to_dict(m) for m in messages],
    }
