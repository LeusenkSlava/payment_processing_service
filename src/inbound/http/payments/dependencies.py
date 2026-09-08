from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.payments.services.create_payment import CreatePaymentService
from src.core.payments.services.get_payment_service import GetPaymentService
from src.outbound.database.dependencies import get_db_session
from src.outbound.database.repositories.payments.outbox_repository import (
    OutboxRepository,
)
from src.outbound.database.repositories.payments.payment_repository import (
    PaymentRepository,
)


def get_create_payment_service(
    session: AsyncSession = Depends(get_db_session),
) -> CreatePaymentService:
    return CreatePaymentService(
        payment_repo=PaymentRepository(session),
        outbox_repo=OutboxRepository(session),
    )


def get_get_payment_service(
    session: AsyncSession = Depends(get_db_session),
) -> GetPaymentService:
    return GetPaymentService(payment_repo=PaymentRepository(session))
