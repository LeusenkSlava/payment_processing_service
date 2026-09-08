import asyncio
import logging

from src.core.payments.services.outbox_relay import OutboxRelayService
from src.outbound.database.dependencies import get_session_scope
from src.outbound.database.repositories.payments.outbox_repository import (
    OutboxRepository,
)
from src.outbound.rabbit_mq.broker import broker
from src.outbound.rabbit_mq.publisher import RabbitMQEventPublisher
from src.outbound.rabbit_mq.topology import PAYMENTS_EXCHANGE

logger = logging.getLogger(__name__)


async def run_outbox_relay_loop(interval: float = 1.0) -> None:
    """
    Фоновый цикл релея outbox-событий.

    :param interval: пауза между итерациями, сек.
    """
    publisher = RabbitMQEventPublisher(broker=broker, exchange=PAYMENTS_EXCHANGE)

    while True:
        try:
            async with get_session_scope() as session:
                repo = OutboxRepository(session)
                relay = OutboxRelayService(outbox_repo=repo, publisher=publisher)
                await relay.relay_once()
        except Exception:
            logger.exception("Outbox relay loop iteration failed")

        await asyncio.sleep(interval)
