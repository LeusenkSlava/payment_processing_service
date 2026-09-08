from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.payments.interfaces import OutboxRepositoryProtocol
from src.core.payments.models.enums import OutboxStatus
from src.core.payments.models.payment import OutboxEvent
from src.outbound.database.models.payments.outbox import OutboxEventModel


class OutboxRepository(OutboxRepositoryProtocol):
    """Репозиторий outbox-событий."""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, event: OutboxEvent) -> OutboxEvent:
        model = OutboxEventModel(
            payment_id=event.payment_id,
            event_type=event.event_type,
            payload=event.payload,
            status=event.status,
        )
        self._session.add(model)
        await self._session.flush()

        event.id = model.id
        return event

    async def get_pending(self, limit: int) -> list[OutboxEvent]:
        stmt = (
            select(OutboxEventModel)
            .where(OutboxEventModel.status == OutboxStatus.PENDING)
            .order_by(OutboxEventModel.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()

        return [
            OutboxEvent(
                id=m.id,
                payment_id=m.payment_id,
                event_type=m.event_type,
                payload=m.payload,
                status=m.status,
            )
            for m in models
        ]

    async def mark_as_sent(self, event_id: int) -> None:
        stmt = (
            update(OutboxEventModel)
            .where(OutboxEventModel.id == event_id)
            .values(status=OutboxStatus.SENT, sent_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)
