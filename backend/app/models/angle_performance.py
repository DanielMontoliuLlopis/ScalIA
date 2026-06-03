import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnglePerformance(Base):
    """Histórico de rendimiento por ángulo × business_type × resultado.

    Se escribe cuando una campaña multi_angle consolida (fase 2/3) o al cerrar
    el ciclo de optimización. Alimenta de vuelta al ResearchAgent/CopyAgent y al
    FunnelTypeSelector (win rate por ángulo). Agregable a nivel de agencia por
    account_id.
    """

    __tablename__ = "angle_performance"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    account_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)

    business_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    angle: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    tipo_oferta: Mapped[str | None] = mapped_column(String(30), nullable=True)

    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    leads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    spend: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    ctr: Mapped[float | None] = mapped_column(Numeric(6, 4), nullable=True)
    cpl: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    roas: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    result: Mapped[str] = mapped_column(String(20), nullable=False)  # winner | loser | inconclusive

    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
