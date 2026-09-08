import logging
from datetime import UTC, datetime

from src.core.payments.interfaces import (
    PaymentGatewayProtocol,
    PaymentRepositoryProtocol,
    WebhookSenderProtocol,
)
from src.core.payments.models.enums import PaymentStatus
from src.core.payments.models.payment import Payment

logger = logging.getLogger(__name__)


class ProcessPaymentService:
    """Обрабатывает платёж обновляет статус, шлёт webhook."""

    def __init__(
        self,
        payment_repo: PaymentRepositoryProtocol,
        gateway: PaymentGatewayProtocol,
        webhook_sender: WebhookSenderProtocol,
    ) -> None:
        self._payment_repo = payment_repo
        self._gateway = gateway
        self._webhook_sender = webhook_sender

    async def execute(self, payment_id: int) -> None:
        payment = await self._payment_repo.get_by_id(payment_id)
        if payment is None:
            logger.warning("Payment %s not found, skipping", payment_id)
            return

        if payment.status in (PaymentStatus.SUCCEEDED, PaymentStatus.FAILED):
            await self._send_webhook(payment)
            return

        locked = await self._payment_repo.update_status(
            payment_id,
            PaymentStatus.PROCESSING,
            expected_current_status=PaymentStatus.PENDING,
        )
        if locked is None:
            logger.info(
                "Payment %s is locked elsewhere, relying on reaper for recovery",
                payment_id,
            )
            return

        succeeded = await self._gateway.charge()
        new_status = PaymentStatus.SUCCEEDED if succeeded else PaymentStatus.FAILED
        processed_at = datetime.now(UTC)

        updated = await self._payment_repo.update_status(
            payment_id,
            new_status,
            processed_at,
            expected_current_status=PaymentStatus.PROCESSING,
        )
        if updated is None:
            logger.info(
                "Payment %s was requeued while processing, skipping stale webhook",
                payment_id,
            )
            return
        await self._send_webhook(updated)

    async def _send_webhook(self, payment: Payment) -> None:
        await self._webhook_sender.send(
            payment.webhook_url,
            {
                "payment_id": payment.id,
                "status": payment.status.value,
                "processed_at": payment.processed_at.isoformat(),
            },
        )
