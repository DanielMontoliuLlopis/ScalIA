import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Closer(Base):
    """Comercial que cierra suscripciones. No es un cliente de la plataforma.

    Atribución cliente → closer vía `User.closer_id`. Las comisiones se generan
    desde el webhook de Stripe (`invoice.paid`), nunca se calculan a mano.
    """

    __tablename__ = "closers"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # % comisión recurrente (mes 2+). 0.06 = 6%.
    commission_rate: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False, default=Decimal("0.06")
    )
    # Código único para link referido: /?ref=CODE
    referral_code: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Acceso al portal del closer (login propio). NULL = sin acceso configurado.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
