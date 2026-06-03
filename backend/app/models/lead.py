import uuid
from datetime import datetime

from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

LEAD_STATUSES = ("new", "contacted", "showed_up", "closed", "lost")


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    landing_page_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("landing_pages.id"), nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str | None] = mapped_column(String(200), nullable=True)
    empresa: Mapped[str | None] = mapped_column(String(200), nullable=True)
    telefono: Mapped[str | None] = mapped_column(String(50), nullable=True)
    num_empleados: Mapped[str | None] = mapped_column(String(50), nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    segment: Mapped[str | None] = mapped_column(String(100), nullable=True)
    scoring_breakdown: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    recommended_action: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    action_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    action_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    lead_status: Mapped[str] = mapped_column(String(50), nullable=False, server_default="new")
    closed_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    meeting_scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    showed_up_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
