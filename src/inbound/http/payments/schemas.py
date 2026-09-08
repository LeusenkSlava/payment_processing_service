from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, HttpUrl

from src.core.payments.models.enums import Currency, PaymentStatus


class PaymentCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2, allow_inf_nan=False)
    currency: Currency
    webhook_url: HttpUrl
    description: str | None = None
    meta_data: dict | None = None


class PaymentResponse(BaseModel):
    payment_id: int
    status: PaymentStatus
    created_at: datetime


class PaymentDetailResponse(BaseModel):
    idempotency_key: str

    id: int
    created_at: datetime
    processed_at: datetime | None

    amount: Decimal
    currency: Currency
    webhook_url: str
    description: str | None
    meta_data: dict | None
    status: PaymentStatus
