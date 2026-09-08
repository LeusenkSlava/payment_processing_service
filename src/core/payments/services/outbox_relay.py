import logging

from src.core.payments.interfaces import (
    EventPublisherProtocol,
    OutboxRepositoryProtocol,
)

logger = logging.getLogger(__name__)


class OutboxRelayService:
    """Публикует накопленные outbox-события в брокер и помечает отправленные."""

    def __init__(
        self,
        outbox_repo: OutboxRepositoryProtocol,
        publisher: EventPublisherProtocol,
        batch_size: int = 50,
    ) -> None:
        self._outbox_repo = outbox_repo
        self._publisher = publisher
        self._batch_size = batch_size

    async def relay_once(self) -> None:
        """Забирает батч PENDING-событий и публикует их."""

        events = await self._outbox_repo.get_pending(limit=self._batch_size)
        for event in events:
            try:
                await self._publisher.publish(event.event_type, event.payload)
                await self._outbox_repo.mark_as_sent(event.id)
            except Exception:
                logger.exception("Failed to relay outbox event %s", event.id)
