from src.core.payments.exceptions import DuplicateIdempotencyKeyError
from src.core.payments.interfaces import (
    OutboxRepositoryProtocol,
    PaymentRepositoryProtocol,
)
from src.core.payments.models.payment import OutboxEvent, Payment


class CreatePaymentService:
    """Создаёт платёж и outbox-событие (outbox pattern)."""

    def __init__(
        self,
        payment_repo: PaymentRepositoryProtocol,
        outbox_repo: OutboxRepositoryProtocol,
    ):
        self._payment_repo = payment_repo
        self._outbox_repo = outbox_repo

    async def execute(self, data, idempotency_key) -> Payment:
        """Создаёт платёж, идемпотентно по idempotency_key.

        :param data: данные платежа из запроса.
        :param idempotency_key: ключ идемпотентности из заголовка.
        :return: созданный либо уже существующий платёж.
        """
        existing = await self._payment_repo.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            return existing

        payment = Payment(
            amount=data.amount,
            currency=data.currency,
            description=data.description,
            idempotency_key=idempotency_key,
            webhook_url=str(data.webhook_url),
            meta_data=data.meta_data,
        )
        try:
            await self._payment_repo.add(payment)
        except DuplicateIdempotencyKeyError:
            return await self._payment_repo.get_by_idempotency_key(idempotency_key)

        outbox_event = OutboxEvent(
            payment_id=payment.id,
            event_type="payments.new",
            payload={
                "payment_id": payment.id,
                "amount": str(payment.amount),
                "currency": payment.currency.value,
            },
        )
        await self._outbox_repo.add(outbox_event)

        return payment
