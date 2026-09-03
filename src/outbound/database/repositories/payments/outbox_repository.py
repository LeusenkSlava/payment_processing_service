from sqlalchemy.ext.asyncio import AsyncSession

from src.core.payments.models.payment import OutboxEvent
from src.outbound.database.models.payments.outbox import OutboxEventModel


class OutboxRepository:
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
