"""Motor de comisiones de closers.

Regla de negocio:
  - 1er pago del cliente  → el closer se lleva el 100% (first_quota).
  - pagos 2+              → el closer se lleva `commission_rate` (6%) — recurrente
                            mientras la suscripción siga activa (sin límite de meses).

Las comisiones nacen SIEMPRE de un pago real (`invoice.paid` de Stripe), nunca se
calculan a mano. `stripe_invoice_id` es único → idempotencia ante reintentos.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.closer import Closer
from app.models.commission import (
    COMMISSION_FIRST_QUOTA,
    COMMISSION_PENDING,
    COMMISSION_RECURRING,
    Commission,
)
from app.models.user import User

logger = logging.getLogger(__name__)

_CENTS = Decimal("0.01")


def _to_amount(cents: int | None) -> Decimal:
    return (Decimal(int(cents or 0)) / Decimal(100)).quantize(_CENTS, rounding=ROUND_HALF_UP)


async def record_commission_from_invoice(db: AsyncSession, invoice: dict) -> Commission | None:
    """Crea (si procede) una comisión a partir de un invoice pagado de Stripe.

    Devuelve la Commission creada, o None si no aplica (sin closer, importe 0,
    o ya registrada).
    """
    invoice_id = invoice.get("id")
    if not invoice_id:
        return None

    amount_cents = invoice.get("amount_paid")
    if not amount_cents or amount_cents <= 0:
        # Invoices de €0 (trial inicial) no generan comisión.
        return None

    customer_id = invoice.get("customer")
    if not customer_id:
        return None

    # Cliente y su closer atribuido
    result = await db.execute(select(User).where(User.stripe_customer_id == customer_id))
    user = result.scalar_one_or_none()
    if not user or not user.closer_id:
        return None

    closer = await db.get(Closer, user.closer_id)
    if not closer or not closer.is_active:
        return None

    # Idempotencia: ¿ya existe comisión para este invoice?
    existing = await db.execute(
        select(Commission.id).where(Commission.stripe_invoice_id == invoice_id)
    )
    if existing.scalar_one_or_none():
        return None

    # nº de pagos previos del cliente que ya generaron comisión
    prior = await db.execute(
        select(func.count(Commission.id)).where(Commission.user_id == user.id)
    )
    prior_count = int(prior.scalar() or 0)

    base_amount = _to_amount(amount_cents)
    if prior_count == 0:
        ctype = COMMISSION_FIRST_QUOTA
        commission_amount = base_amount  # 100% del primer pago
    else:
        ctype = COMMISSION_RECURRING
        commission_amount = (base_amount * Decimal(closer.commission_rate)).quantize(
            _CENTS, rounding=ROUND_HALF_UP
        )

    period_start = _period_start(invoice)

    commission = Commission(
        closer_id=closer.id,
        user_id=user.id,
        stripe_invoice_id=invoice_id,
        type=ctype,
        base_amount=base_amount,
        commission_amount=commission_amount,
        currency=(invoice.get("currency") or "eur"),
        period_start=period_start,
        status=COMMISSION_PENDING,
    )
    db.add(commission)
    await db.commit()
    await db.refresh(commission)
    logger.info(
        "Comisión %s creada: closer=%s cliente=%s invoice=%s base=%s comision=%s",
        ctype, closer.id, user.id, invoice_id, base_amount, commission_amount,
    )
    return commission


def _period_start(invoice: dict) -> datetime | None:
    lines = (invoice.get("lines") or {}).get("data") or []
    for line in lines:
        period = line.get("period") or {}
        start = period.get("start")
        if start:
            return datetime.fromtimestamp(start, tz=timezone.utc)
    created = invoice.get("created")
    if created:
        return datetime.fromtimestamp(created, tz=timezone.utc)
    return None
