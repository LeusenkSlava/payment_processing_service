from datetime import datetime
from decimal import Decimal

from sqlalchemy import Enum, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.payments.models.enums import Currency, PaymentStatus
from src.outbound.database.models.base_model import BaseModel


class PaymentModel(BaseModel):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_payments_idempotency_key"),
    )

    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, native_enum=True),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    meta_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=True),
        nullable=False,
        default=PaymentStatus.PENDING,
    )

    webhook_url: Mapped[str] = mapped_column(String(2048), nullable=False)

    processed_at: Mapped[datetime | None] = mapped_column(nullable=True)
