from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.payments.models.enums import OutboxStatus
from src.outbound.database.models.base_model import BaseModel


class OutboxEventModel(BaseModel):
    __tablename__ = "outbox_events"

    payment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False
    )

    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    status: Mapped[OutboxStatus] = mapped_column(
        Enum(OutboxStatus, native_enum=True),
        nullable=False,
        default=OutboxStatus.PENDING,
    )

    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)
