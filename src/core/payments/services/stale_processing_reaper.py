import logging

from src.core.payments.interfaces import (
    OutboxRepositoryProtocol,
    PaymentRepositoryProtocol,
)
from src.core.payments.models.payment import OutboxEvent

logger = logging.getLogger(__name__)


class StaleProcessingReaper:
    """Возвращает зависшие в PROCESSING платежи в оборот через outbox
    та же at-least-once гарантия, что и у создания платежа, без прямой
    публикации в брокер."""

    def __init__(
        self,
        payment_repo: PaymentRepositoryProtocol,
        outbox_repo: OutboxRepositoryProtocol,
        lease_seconds: int,
        batch_size: int = 50,
    ) -> None:
        self._payment_repo = payment_repo
        self._outbox_repo = outbox_repo
        self._lease_seconds = lease_seconds
        self._batch_size = batch_size

    async def reap_once(self) -> None:
        stale_ids = await self._payment_repo.requeue_stale_processing(
            older_than_seconds=self._lease_seconds, limit=self._batch_size
        )
        for payment_id in stale_ids:
            await self._outbox_repo.add(
                OutboxEvent(
                    payment_id=payment_id,
                    event_type="payments.new",
                    payload={"payment_id": payment_id},
                )
            )
        if stale_ids:
            logger.warning(
                "Requeued %d stale processing payments: %s", len(stale_ids), stale_ids
            )
