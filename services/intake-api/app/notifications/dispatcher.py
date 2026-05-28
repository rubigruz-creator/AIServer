import logging
from typing import Any

from app.config import WEBHOOK_URL
from app.notifications.webhook import send_webhook

logger = logging.getLogger(__name__)


async def notify_application_created(payload: dict[str, Any]) -> None:
    """Точка расширения: сюда позже добавят MAX, Telegram, email."""
    if WEBHOOK_URL:
        try:
            await send_webhook(WEBHOOK_URL, payload)
        except Exception:
            logger.exception("Webhook notification failed")
    logger.info(
        "application_created conversation=%s phone=%s",
        payload.get("conversation_id"),
        payload.get("client_phone"),
    )
