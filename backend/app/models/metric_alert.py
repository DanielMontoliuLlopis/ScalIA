import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MetricAlert(Base):
    """Alerta automática detectada sobre metric_snapshots (no es LLM).

    La genera el worker de métricas tras cada sync: compara la ventana reciente
    contra su baseline y dispara cuando una regla salta (CPL sube, ROAS bajo,
    gasto sin leads, CTR cae). Idempotente por (plan, tipo, día) para no duplicar.
    A diferencia de `recommendations` (OptimizationAgent, propone acción a aprobar),
    una alerta solo avisa — el usuario la lee y la descarta.
    """

    __tablename__ = "metric_alerts"
    __table_args__ = (
        UniqueConstraint("plan_id", "type", "snapshot_date", name="uq_metric_alert_identity"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False, index=True
    )

    # cpl_spike | roas_low | spend_no_leads | ctr_drop
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    severity: Mapped[str] = mapped_column(String(10), nullable=False, default="warning")  # info|warning|critical
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    metric_key: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    current_value: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)
    baseline_value: Mapped[float | None] = mapped_column(Numeric(12, 4), nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active|dismissed
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
