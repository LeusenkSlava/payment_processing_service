from faststream.rabbit import RabbitBroker

from src.main.config.settings import settings
from src.outbound.rabbit_mq.topology import (
    DLQ_QUEUE,
    DLX_EXCHANGE,
    NEW_PAYMENT_QUEUE,
    PAYMENTS_EXCHANGE,
    RETRY_EXCHANGE,
    RETRY_QUEUES,
)

broker = RabbitBroker(settings.rabbitmq.dsn)


async def setup_topology() -> None:
    exchange = await broker.declare_exchange(PAYMENTS_EXCHANGE)
    retry_exchange = await broker.declare_exchange(RETRY_EXCHANGE)
    dlx_exchange = await broker.declare_exchange(DLX_EXCHANGE)

    new_queue = await broker.declare_queue(NEW_PAYMENT_QUEUE)
    dlq_queue = await broker.declare_queue(DLQ_QUEUE)

    await new_queue.bind(exchange, routing_key="payments.new")
    await dlq_queue.bind(dlx_exchange, routing_key="payments.dlq")

    for queue_def in RETRY_QUEUES:
        queue = await broker.declare_queue(queue_def)
        await queue.bind(retry_exchange, routing_key=queue_def.routing_key)
