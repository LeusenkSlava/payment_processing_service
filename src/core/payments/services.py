from src.core.payments.interfaces import OutboxRepository, PaymentRepository
from src.core.payments.models.payment import OutboxEvent, Payment


class CreatePaymentService:
    def __init__(self, payment_repo: PaymentRepository, outbox_repo: OutboxRepository):
        self._payment_repo = payment_repo
        self._outbox_repo = outbox_repo

    async def execute(self, data, idempotency_key) -> Payment:
        payment = Payment(
            amount=data.amount,
            currency=data.currency,
            idempotency_key=idempotency_key,
            webhook_url=data.webhook_url,
            meta_data=data.meta_data,
        )
        await self._payment_repo.add(payment)

        outbox_event = OutboxEvent(
            payment_id=payment.id,
            event_type="payment.created",
            payload={
                "payment_id": payment.id,
                "amount": str(payment.amount),
                "currency": payment.currency.value,
            },
        )
        await self._outbox_repo.add(outbox_event)

        return payment
