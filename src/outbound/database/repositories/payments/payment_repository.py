from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.payments.exceptions import DuplicateIdempotencyKeyError
from src.core.payments.interfaces import PaymentRepositoryProtocol
from src.core.payments.models.enums import PaymentStatus
from src.core.payments.models.payment import Payment
from src.outbound.database.models.payments.payment import PaymentModel


class PaymentRepository(PaymentRepositoryProtocol):
    """Репозиторий платежей."""

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

        try:
            async with self._session.begin_nested():
                await self._session.flush()
        except IntegrityError as exc:
            raise DuplicateIdempotencyKeyError(payment.idempotency_key) from exc

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

    async def update_status(
        self,
        payment_id: int,
        status: PaymentStatus,
        processed_at: datetime | None = None,
        *,
        expected_current_status: PaymentStatus | None = None,
    ) -> Payment | None:
        stmt = update(PaymentModel).where(PaymentModel.id == payment_id)

        if expected_current_status is not None:
            if isinstance(expected_current_status, PaymentStatus):
                stmt = stmt.where(PaymentModel.status == expected_current_status)
            else:
                stmt = stmt.where(PaymentModel.status.in_(expected_current_status))

        values = {"status": status}
        if processed_at is not None:
            values["processed_at"] = processed_at

        stmt = stmt.values(**values).returning(PaymentModel)

        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()

        if model is None:
            return None

        await self._session.commit()
        return self._to_entity(model)

    async def requeue_stale_processing(
        self, older_than_seconds: int, limit: int
    ) -> list[int]:
        threshold = datetime.now(UTC) - timedelta(seconds=older_than_seconds)

        select_stmt = (
            select(PaymentModel.id)
            .where(
                PaymentModel.status == PaymentStatus.PROCESSING,
                PaymentModel.updated_at < threshold,
            )
            .order_by(PaymentModel.updated_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        ids = list((await self._session.execute(select_stmt)).scalars().all())
        if not ids:
            return []

        await self._session.execute(
            update(PaymentModel)
            .where(PaymentModel.id.in_(ids))
            .values(status=PaymentStatus.PENDING)
        )
        await self._session.flush()
        return ids

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
