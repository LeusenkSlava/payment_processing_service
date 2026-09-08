import logging

from src.outbound.rabbit_mq.broker import broker
from src.outbound.rabbit_mq.topology import DLQ_QUEUE, DLX_EXCHANGE

logger = logging.getLogger(__name__)


@broker.subscriber(queue=DLQ_QUEUE, exchange=DLX_EXCHANGE)
async def handle_payment_dlq(body: dict) -> None:
    payment_id = body.get("payment_id")
    logger.error("Payment %s permanently failed after all retry attempts", payment_id)
