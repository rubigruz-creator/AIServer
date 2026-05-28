import httpx


async def send_webhook(url: str, payload: dict) -> None:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
