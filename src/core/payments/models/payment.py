from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from src.core.payments.models.enums import Currency, OutboxStatus, PaymentStatus


@dataclass
class OutboxEvent:
    payment_id: int
    event_type: str
    payload: dict
    status: OutboxStatus = OutboxStatus.PENDING

    id: int | None = None
    sent_at: datetime | None = None


@dataclass
class Payment:
    idempotency_key: str
    amount: Decimal
    currency: Currency
    webhook_url: str
    description: str | None = None
    meta_data: dict | None = None
    status: PaymentStatus = PaymentStatus.PENDING

    id: int | None = None
    created_at: datetime | None = None
    processed_at: datetime | None = None
