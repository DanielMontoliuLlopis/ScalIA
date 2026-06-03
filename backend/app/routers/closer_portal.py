"""Portal del closer: login propio + dashboard mensual de sus comisiones.

Cada closer solo ve SUS clientes y SUS comisiones. Autenticación independiente
de la de usuarios (token `typ=closer`).
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import create_closer_token, get_current_closer, verify_password
from app.config import settings
from app.database import get_db
from app.models.closer import Closer
from app.models.commission import COMMISSION_FIRST_QUOTA, COMMISSION_PAID, Commission
from app.models.user import User
from app.schemas.closer_portal import (
    CloserDashboard,
    CloserLoginRequest,
    CloserMe,
    CloserTokenResponse,
    MonthlyCommission,
)

router = APIRouter(prefix="/closer-portal", tags=["closer-portal"])

_MONTHS_ES = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic",
]


def _cents(amount: Decimal | int | float | None) -> int:
    if amount is None:
        return 0
    return int((Decimal(str(amount)) * 100).to_integral_value())


@router.post("/login", response_model=CloserTokenResponse)
async def closer_login(
    body: CloserLoginRequest, db: AsyncSession = Depends(get_db)
) -> CloserTokenResponse:
    result = await db.execute(select(Closer).where(Closer.email == body.email))
    closer = result.scalar_one_or_none()
    if not closer or not closer.hashed_password or not verify_password(
        body.password, closer.hashed_password
    ):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    if not closer.is_active:
        raise HTTPException(status_code=403, detail="Cuenta de closer desactivada")
    return CloserTokenResponse(access_token=create_closer_token(closer.id))


@router.get("/me", response_model=CloserMe)
async def closer_me(closer: Closer = Depends(get_current_closer)) -> CloserMe:
    return CloserMe(
        id=closer.id,
        full_name=closer.full_name,
        email=closer.email,
        commission_rate=float(closer.commission_rate),
        referral_code=closer.referral_code,
        is_active=closer.is_active,
    )


@router.get("/dashboard", response_model=CloserDashboard)
async def closer_dashboard(
    closer: Closer = Depends(get_current_closer), db: AsyncSession = Depends(get_db)
) -> CloserDashboard:
    # Clientes atribuidos
    clients_count = int(
        (await db.execute(select(func.count(User.id)).where(User.closer_id == closer.id))).scalar()
        or 0
    )
    active_clients = int(
        (
            await db.execute(
                select(func.count(User.id)).where(
                    User.closer_id == closer.id,
                    User.subscription_status.in_(("active", "trialing", "past_due")),
                )
            )
        ).scalar()
        or 0
    )

    # Comisiones del closer
    comms = list(
        (
            await db.execute(select(Commission).where(Commission.closer_id == closer.id))
        ).scalars()
    )

    buckets: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "count": 0,
            "first_quota_cents": 0,
            "recurring_cents": 0,
            "total_cents": 0,
            "pending_cents": 0,
            "paid_cents": 0,
        }
    )
    total_earned = pending_total = paid_total = 0

    for c in comms:
        when: datetime = c.period_start or c.created_at
        key = f"{when.year:04d}-{when.month:02d}"
        amount = _cents(c.commission_amount)
        b = buckets[key]
        b["count"] += 1
        b["total_cents"] += amount
        if c.type == COMMISSION_FIRST_QUOTA:
            b["first_quota_cents"] += amount
        else:
            b["recurring_cents"] += amount
        if c.status == COMMISSION_PAID:
            b["paid_cents"] += amount
            paid_total += amount
        else:
            b["pending_cents"] += amount
            pending_total += amount
        total_earned += amount

    months = [
        MonthlyCommission(
            month=key,
            label=f"{_MONTHS_ES[int(key[5:7]) - 1]} {key[:4]}",
            count=b["count"],
            first_quota_cents=b["first_quota_cents"],
            recurring_cents=b["recurring_cents"],
            total_cents=b["total_cents"],
            pending_cents=b["pending_cents"],
            paid_cents=b["paid_cents"],
        )
        for key, b in sorted(buckets.items(), reverse=True)
    ]

    return CloserDashboard(
        currency=settings.STRIPE_CURRENCY,
        clients_count=clients_count,
        active_clients_count=active_clients,
        total_earned_cents=total_earned,
        pending_cents=pending_total,
        paid_cents=paid_total,
        months=months,
    )
