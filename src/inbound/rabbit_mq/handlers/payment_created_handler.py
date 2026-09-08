import logging

from faststream.rabbit import RabbitMessage

from src.core.payments.services.process_payment_service import ProcessPaymentService
from src.outbound.database.dependencies import get_session_scope
from src.outbound.database.repositories.payments.payment_repository import (
    PaymentRepository,
)
from src.outbound.payment_gateway.emulator import PaymentGatewayEmulator
from src.outbound.rabbit_mq.broker import broker
from src.outbound.rabbit_mq.topology import (
    DLX_EXCHANGE,
    MAX_RETRY_ATTEMPTS,
    NEW_PAYMENT_QUEUE,
    PAYMENTS_EXCHANGE,
    RETRY_EXCHANGE,
)
from src.outbound.rabbit_mq.utils import RETRY_ATTEMPT_HEADER, get_retry_attempt
from src.outbound.webhook.client import http_client
from src.outbound.webhook.sender import HttpWebhookSender

logger = logging.getLogger(__name__)


@broker.subscriber(queue=NEW_PAYMENT_QUEUE, exchange=PAYMENTS_EXCHANGE)
async def handle_payment_created(body: dict, message: RabbitMessage) -> None:
    """
    Обрабатывает событие создания платежа.

    При ошибке публикует сообщение в retry-очередь (с задержкой через TTL)
    либо в DLQ, если попытки исчерпаны.
    """
    payment_id = body["payment_id"]

    try:
        async with get_session_scope() as session:
            service = ProcessPaymentService(
                payment_repo=PaymentRepository(session),
                gateway=PaymentGatewayEmulator(),
                webhook_sender=HttpWebhookSender(http_client),
            )
            await service.execute(payment_id)

    except Exception:
        attempt = get_retry_attempt(message.raw_message.headers)
        logger.exception(
            "Failed to process payment %s (attempt %d)", payment_id, attempt
        )
        await _schedule_retry_or_dlq(body, attempt, payment_id)


async def _schedule_retry_or_dlq(body: dict, attempt: int, payment_id: int) -> None:
    if attempt >= MAX_RETRY_ATTEMPTS:
        await broker.publish(
            body,
            exchange=DLX_EXCHANGE,
            routing_key="payments.dlq",
            persist=True,
        )
        logger.error("Payment %s moved to DLQ after %d attempts", payment_id, attempt)
    else:
        next_attempt = attempt + 1
        await broker.publish(
            body,
            exchange=RETRY_EXCHANGE,
            routing_key=f"retry.{next_attempt}",
            headers={RETRY_ATTEMPT_HEADER: next_attempt},
            persist=True,
        )
        logger.warning("Payment %s scheduled for retry %d", payment_id, next_attempt)
