from faststream.rabbit import RabbitBroker, RabbitExchange

from src.core.payments.interfaces import EventPublisherProtocol


class RabbitMQEventPublisher(EventPublisherProtocol):
    """Реализация на RabbitMQ (FastStream)."""

    def __init__(self, broker: RabbitBroker, exchange: RabbitExchange) -> None:
        self._broker = broker
        self._exchange = exchange

    async def publish(self, routing_key: str, payload: dict) -> None:
        await self._broker.publish(
            payload,
            exchange=self._exchange,
            routing_key=routing_key,
            persist=True,
        )
