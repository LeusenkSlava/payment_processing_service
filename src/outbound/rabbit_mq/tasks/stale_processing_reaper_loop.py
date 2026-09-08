import asyncio
import logging

from src.core.payments.services.stale_processing_reaper import StaleProcessingReaper
from src.main.config.settings import settings
from src.outbound.database.dependencies import get_session_scope
from src.outbound.database.repositories.payments.outbox_repository import (
    OutboxRepository,
)
from src.outbound.database.repositories.payments.payment_repository import (
    PaymentRepository,
)

logger = logging.getLogger(__name__)


async def run_stale_processing_reaper_loop(
    interval: float = 10.0,
) -> None:
    while True:
        try:
            async with get_session_scope() as session:
                reaper = StaleProcessingReaper(
                    payment_repo=PaymentRepository(session),
                    outbox_repo=OutboxRepository(session),
                    lease_seconds=settings.app.PROCESSING_LEASE_SECONDS,
                )
                await reaper.reap_once()
        except Exception:
            logger.exception("Stale processing reaper loop iteration failed")

        await asyncio.sleep(interval)
