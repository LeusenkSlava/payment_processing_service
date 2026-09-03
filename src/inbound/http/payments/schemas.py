from decimal import Decimal

from pydantic import BaseModel, Field

from src.core.payments.models.enums import Currency, PaymentStatus


class PaymentCreateRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    currency: Currency
    description: str
    meta_data: dict | None
    webhook_url: str


class PaymentResponse(BaseModel):
    payment_id: int
    status: PaymentStatus
