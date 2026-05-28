import secrets
import uuid
from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

from app import applications as app_parser
from app.config import ADMIN_PASSWORD, ADMIN_USER
from app.db import get_conn, init_db, row_to_dict, utc_now_iso
from app.notifications import notify_application_created

app = FastAPI(title="AIServer Intake API", version="1.0.0")
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
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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
) -> dict[str, Any]:
    limit = min(max(limit, 1), 500)
    offset = max(offset, 0)
    where = "WHERE has_application = 1" if applications_only else ""
    with get_conn() as conn:
        rows = conn.execute(
            f"""
            SELECT c.*,
                   (SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) AS message_count
            FROM conversations c
            {where}
            ORDER BY c.created_at DESC
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
