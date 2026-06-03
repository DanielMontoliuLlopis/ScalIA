import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# type
COMMISSION_FIRST_QUOTA = "first_quota"  # 1er pago del cliente → 100%
COMMISSION_RECURRING = "recurring"      # pagos 2+ → commission_rate (6%)

# status
COMMISSION_PENDING = "pending"
COMMISSION_PAID = "paid"


class Commission(Base):
    """Una comisión por cada pago real del cliente (un `invoice.paid` de Stripe).

    `stripe_invoice_id` es único → idempotencia ante reintentos de webhook.
    """

    __tablename__ = "commissions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    closer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("closers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stripe_invoice_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )

    type: Mapped[str] = mapped_column(String(20), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    commission_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, default="eur")
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default=COMMISSION_PENDING)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
