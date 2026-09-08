from src.inbound.rabbit_mq.handlers.payment_created_handler import (
    handle_payment_created,
)
from src.inbound.rabbit_mq.handlers.payment_dlq_handler import handle_payment_dlq

__all__ = (
    "handle_payment_created",
    "handle_payment_dlq",
)


def register_handlers() -> None:
    """Метод для регистрации обработчиков сообщений RabbitMQ."""
