import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    business_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Tier de suscripción: canceled (sin acceso) | research_10 | research_100 | starter | growth | agency
    # No hay trial gratuito: sin suscripción activa = "canceled" = cero acceso.
    plan: Mapped[str] = mapped_column(String(20), nullable=False, default="canceled")
    active_campaigns_limit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # Research Mode — saldo de escaneos del ciclo actual (se reinicia cada periodo, no acumula)
    scans_remaining: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    scans_reset_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Rol de equipo dentro de una cuenta: owner | admin | member | viewer
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="owner")
    # Si es sub-usuario, apunta al dueño de la cuenta (owner). NULL = cuenta propia.
    parent_account_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    # Programa Fundadores: precio bloqueado de por vida
    is_founder: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Superadmin de plataforma (acceso al panel /admin). Distinto de `role` (por cuenta).
    is_superadmin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Closer que cerró esta suscripción (atribución para comisiones). NULL = sin closer.
    closer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("closers.id", ondelete="SET NULL"), nullable=True, index=True
    )

    stripe_customer_id: Mapped[str | None] = mapped_column(
        String(100), nullable=True, unique=True, index=True
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subscription_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    subscription_current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
