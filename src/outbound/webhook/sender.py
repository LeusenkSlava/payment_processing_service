import httpx

from src.core.payments.interfaces import WebhookSenderProtocol

REQUEST_TIMEOUT_SECONDS = 10.0


class HttpWebhookSender(WebhookSenderProtocol):
    """Реализация на httpx."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def send(self, url: str, payload: dict) -> None:
        response = await self._client.post(
            url,
            json=payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
