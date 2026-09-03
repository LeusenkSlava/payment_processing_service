from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.payments.models.payment import Payment
from src.outbound.database.models.payments.payment import PaymentModel


class PaymentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, payment: Payment) -> Payment:
        model = PaymentModel(
            idempotency_key=payment.idempotency_key,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            meta_data=payment.meta_data,
            webhook_url=payment.webhook_url,
            status=payment.status,
        )
        self._session.add(model)
        await self._session.flush()

        payment.id = model.id
        payment.created_at = model.created_at
        return payment

    async def get_by_id(self, payment_id: int) -> Payment | None:
        model = await self._session.get(PaymentModel, payment_id)
        return self._to_entity(model) if model else None

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        stmt = select(PaymentModel).where(PaymentModel.idempotency_key == key)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(model: PaymentModel) -> Payment:
        return Payment(
            idempotency_key=model.idempotency_key,
            amount=model.amount,
            currency=model.currency,
            webhook_url=model.webhook_url,
            description=model.description,
            meta_data=model.meta_data,
            status=model.status,
            id=model.id,
            created_at=model.created_at,
            processed_at=model.processed_at,
        )
