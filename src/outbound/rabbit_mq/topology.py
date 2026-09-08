from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue

PAYMENTS_EXCHANGE = RabbitExchange("payments", type=ExchangeType.TOPIC, durable=True)
RETRY_EXCHANGE = RabbitExchange("payments.retry", type=ExchangeType.TOPIC, durable=True)
DLX_EXCHANGE = RabbitExchange("payments.dlx", type=ExchangeType.TOPIC, durable=True)

NEW_PAYMENT_QUEUE = RabbitQueue(
    "payments.new",
    durable=True,
    routing_key="payments.new",
)

DLQ_QUEUE = RabbitQueue(
    "payments.dlq",
    durable=True,
    routing_key="payments.dlq",
)

RETRY_TTLS_MS = (2_000, 4_000, 8_000)
MAX_RETRY_ATTEMPTS = len(RETRY_TTLS_MS)

RETRY_QUEUES = [
    RabbitQueue(
        f"payments.retry.{attempt}",
        durable=True,
        routing_key=f"retry.{attempt}",
        arguments={
            "x-message-ttl": ttl_ms,
            "x-dead-letter-exchange": PAYMENTS_EXCHANGE.name,
            "x-dead-letter-routing-key": "payments.new",
        },
    )
    for attempt, ttl_ms in enumerate(RETRY_TTLS_MS, start=1)
]
