import uuid
from datetime import date, datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MetricSnapshot(Base):
    """Snapshot diario de métricas Meta Insights por entidad (campaña/ad set/ad)
    y opcionalmente por breakdown (edad, género, placement, región, dispositivo).

    Lo escribe el worker `sync_metrics_for_all_campaigns` (Celery beat, cada hora)
    con `time_increment=1`, de forma idempotente (upsert por clave única). Es la
    fuente de verdad para series temporales, comparación de periodos, breakdowns
    y detección de anomalías — el dashboard lee de aquí, no pega a Meta en vivo.

    Idempotencia: las columnas de identidad y breakdown usan "" en lugar de NULL
    para que el UNIQUE compuesto funcione limpio (NULL no colisiona en Postgres).
    """

    __tablename__ = "metric_snapshots"
    __table_args__ = (
        UniqueConstraint(
            "plan_id",
            "level",
            "meta_adset_id",
            "meta_ad_id",
            "breakdown_key",
            "breakdown_value",
            "snapshot_date",
            name="uq_metric_snapshot_identity",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True
    )
    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False, index=True
    )

    # ── Identidad Meta ────────────────────────────────────────────────────────
    meta_campaign_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    meta_adset_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    meta_ad_id: Mapped[str] = mapped_column(String(100), nullable=False, default="")
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # campaign | adset | ad
    # Ángulo (multi_angle): se deriva del ad set vía plan.angles_tested
    angle: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)

    # ── Breakdown ─────────────────────────────────────────────────────────────
    # breakdown_key: "" (sin breakdown) | age | gender | publisher_platform |
    #                region | impression_device
    breakdown_key: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    breakdown_value: Mapped[str] = mapped_column(String(120), nullable=False, default="")

    # ── Periodo (día de los datos, time_increment=1) ──────────────────────────
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # ── Métricas crudas ───────────────────────────────────────────────────────
    impressions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clicks: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reach: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    leads: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conversions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    spend: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    revenue: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)

    # ── Métricas derivadas (de Meta cuando vienen, si no calculadas) ──────────
    ctr: Mapped[float | None] = mapped_column(Numeric(8, 4), nullable=True)
    cpc: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    cpm: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    cpl: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)

    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
