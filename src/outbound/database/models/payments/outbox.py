from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.payments.models.enums import OutboxStatus
from src.outbound.database.models.base_model import BaseModel


class OutboxEventModel(BaseModel):
    __tablename__ = "outbox_events"
    __table_args__ = (
        Index(
            "ix_outbox_events_status_created_at",
            "status",
            "created_at",
            postgresql_where=text(f"status = '{OutboxStatus.PENDING.value}'"),
        ),
    )

    payment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False
    )

    event_type: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)

    status: Mapped[OutboxStatus] = mapped_column(
        Enum(
            OutboxStatus,
            native_enum=True,
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=OutboxStatus.PENDING.value,
    )
    sent_at: Mapped[datetime | None] = mapped_column(nullable=True)
