import datetime
from typing import Protocol

from src.core.payments.models.enums import PaymentStatus
from src.core.payments.models.payment import OutboxEvent, Payment


class PaymentRepositoryProtocol(Protocol):
    """Репозиторий платежей."""

    async def add(self, payment: Payment) -> None:
        """Сохраняет новый платёж.

        :param payment: платёж для сохранения.
        :raises DuplicateIdempotencyKeyError: если idempotency_key уже занят.
        """
        ...

    async def get_by_id(self, payment_id: int) -> Payment | None:
        """Возвращает платёж по id.

        :param payment_id: id платежа.
        :return: платёж либо None, если не найден.
        """
        ...

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        """Возвращает платёж по ключу идемпотентности.

        :param key: idempotency_key.
        :return: платёж либо None, если не найден.
        """
        ...

    async def update_status(
        self,
        payment_id: int,
        status: PaymentStatus,
        processed_at: datetime.datetime | None = None,
        *,
        expected_current_status: PaymentStatus | None = None,
    ) -> Payment | None:
        """Обновляет статус платежа.

        :param payment_id: id платежа.
        :param status: новый статус.
        :param processed_at: время обработки (для терминальных статусов).
        :param expected_current_status: обновление произойдёт
            только если текущий статус в БД совпадает с этим значением
        :return: обновлённый платёж, либо None если expected_current_status
            указан и не совпал.
        """
        ...

    async def requeue_stale_processing(
        self, older_than_seconds: int, limit: int
    ) -> list[int]:
        """Находит зависшие в PROCESSING платежи, возвращает их в PENDING.

        :param older_than_seconds: порог "протухания" processing, сек.
        :param limit: максимум записей за итерацию.
        :return: id платежей, возвращённых в PENDING.
        """
        ...


class OutboxRepositoryProtocol(Protocol):
    """Репозиторий outbox-событий."""

    async def add(self, event: OutboxEvent) -> None:
        """
        Сохраняет новое событие со статусом PENDING.

        :param event: событие для сохранения.
        """
        ...

    async def get_pending(self, limit: int) -> list[OutboxEvent]:
        """
        Возвращает список pending событий.

        :param limit: максимальное количество событий для возврата.
        :return: список pending событий.
        """
        ...

    async def mark_as_sent(self, event_id: int) -> None:
        """Помечает событие как отправленное.

        :param event_id: id события.
        """
        ...


class EventPublisherProtocol(Protocol):
    """Публикатор событий в брокер."""

    async def publish(self, routing_key: str, payload: dict) -> None:
        """Публикует событие.

        :param routing_key: routing key сообщения.
        :param payload: тело сообщения.
        """
        ...


class PaymentGatewayProtocol(Protocol):
    """Платёжный шлюз."""

    async def charge(self) -> bool:
        """Выполняет списание.

        :return: True при успехе, False при отказе шлюза.
        """
        ...


class WebhookSenderProtocol(Protocol):
    """Отправитель webhook-уведомлений."""

    async def send(self, url: str, payload: dict) -> None:
        """Отправляет webhook.

        :param url: адрес получателя.
        :param payload: тело уведомления.
        :raises httpx.HTTPStatusError: при ошибке ответа (4xx/5xx).
        """
        ...
