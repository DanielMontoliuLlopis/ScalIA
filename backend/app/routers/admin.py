"""Panel de administración de plataforma. Solo superadmins.

Gestión de closers (comerciales), atribución de clientes y liquidación de
comisiones. Las comisiones se generan automáticamente desde el webhook de
Stripe (`invoice.paid`); aquí solo se consultan y se marcan como pagadas.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone, date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import secrets

from app.auth import get_current_admin, hash_password
from app.models.plan import Plan
from app.config import settings
from app.database import get_db
from app.models.closer import Closer
from app.models.commission import COMMISSION_PAID, COMMISSION_PENDING, Commission
from app.models.user import User
from app.schemas.admin import (
    AdminClientRow,
    AdminClientUpdate,
    AdminOverview,
    AssignCloserRequest,
    CloserCreate,
    CloserCreated,
    CloserDetail,
    CloserRow,
    CloserUpdate,
    CommissionRow,
    LiquidateRequest,
    LiquidateResponse,
    ResetPasswordResponse,
)
from app.services import stripe_service
from app.services.closers import generate_referral_code

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(get_current_admin)])

_ACTIVE_STATUSES = ("active", "trialing", "past_due")


def _cents(amount: Decimal | int | float | None) -> int:
    if amount is None:
        return 0
    return int((Decimal(str(amount)) * 100).to_integral_value())


def _user_mrr_cents(user: User) -> int:
    """MRR aproximado de un usuario según su tier (founder o normal)."""
    if user.is_superadmin:
        return 0
    if user.subscription_status not in _ACTIVE_STATUSES:
        return 0
    plan_def = stripe_service.PLAN_DEFS.get(user.plan)
    if plan_def:
        return int(plan_def["founder_amount"] if user.is_founder else plan_def["amount"])
    research_def = stripe_service.RESEARCH_PLAN_DEFS.get(user.plan)
    if research_def:
        return int(research_def["amount"])
    return 0


# ── Overview ──────────────────────────────────────────────────────────────────
@router.get("/overview", response_model=AdminOverview)
async def overview(db: AsyncSession = Depends(get_db)) -> AdminOverview:
    total_users = int(
        (await db.execute(select(func.count(User.id)).where(User.parent_account_id.is_(None)))).scalar()
        or 0
    )

    active_users_res = await db.execute(
        select(User).where(User.subscription_status.in_(_ACTIVE_STATUSES))
    )
    active_users = list(active_users_res.scalars())
    mrr = sum(_user_mrr_cents(u) for u in active_users)

    total_closers = int((await db.execute(select(func.count(Closer.id)))).scalar() or 0)
    active_closers = int(
        (await db.execute(select(func.count(Closer.id)).where(Closer.is_active.is_(True)))).scalar()
        or 0
    )

    pending = (
        await db.execute(
            select(func.coalesce(func.sum(Commission.commission_amount), 0)).where(
                Commission.status == COMMISSION_PENDING
            )
        )
    ).scalar()
    paid = (
        await db.execute(
            select(func.coalesce(func.sum(Commission.commission_amount), 0)).where(
                Commission.status == COMMISSION_PAID
            )
        )
    ).scalar()

    return AdminOverview(
        total_users=total_users,
        active_subscriptions=len(active_users),
        mrr_cents=mrr,
        currency=settings.STRIPE_CURRENCY,
        total_closers=total_closers,
        active_closers=active_closers,
        commissions_pending_cents=_cents(pending),
        commissions_paid_cents=_cents(paid),
    )


# ── Clientes ──────────────────────────────────────────────────────────────────
async def _closer_name_map(db: AsyncSession) -> dict[uuid.UUID, str]:
    rows = (await db.execute(select(Closer.id, Closer.full_name))).all()
    return {r[0]: r[1] for r in rows}


@router.get("/users", response_model=list[AdminClientRow])
async def list_users(db: AsyncSession = Depends(get_db)) -> list[AdminClientRow]:
    result = await db.execute(
        select(User).where(User.parent_account_id.is_(None)).order_by(User.created_at.desc())
    )
    users = list(result.scalars())
    names = await _closer_name_map(db)
    return [
        AdminClientRow(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            plan=u.plan,
            subscription_status=u.subscription_status,
            is_founder=u.is_founder,
            closer_id=u.closer_id,
            closer_name=names.get(u.closer_id) if u.closer_id else None,
            mrr_cents=_user_mrr_cents(u),
            created_at=u.created_at,
        )
        for u in users
    ]


def _client_row(user: User, closer_name: str | None) -> AdminClientRow:
    return AdminClientRow(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        plan=user.plan,
        subscription_status=user.subscription_status,
        is_founder=user.is_founder,
        closer_id=user.closer_id,
        closer_name=closer_name,
        mrr_cents=_user_mrr_cents(user),
        created_at=user.created_at,
    )


_VALID_PLANS = set(stripe_service.PLAN_DEFS) | set(stripe_service.RESEARCH_PLAN_DEFS) | {"free"}
_VALID_STATUSES = set(_ACTIVE_STATUSES) | {"canceled", "incomplete", "unpaid", "inactive", None}


@router.patch("/users/{user_id}/closer", response_model=AdminClientRow)
async def assign_closer(
    user_id: uuid.UUID,
    body: AssignCloserRequest,
    db: AsyncSession = Depends(get_db),
) -> AdminClientRow:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    closer_name = None
    if body.closer_id is not None:
        closer = await db.get(Closer, body.closer_id)
        if not closer:
            raise HTTPException(status_code=404, detail="Closer no encontrado")
        closer_name = closer.full_name

    user.closer_id = body.closer_id
    await db.commit()
    await db.refresh(user)
    return _client_row(user, closer_name)


@router.patch("/users/{user_id}", response_model=AdminClientRow)
async def update_user(
    user_id: uuid.UUID,
    body: AdminClientUpdate,
    db: AsyncSession = Depends(get_db),
) -> AdminClientRow:
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if body.plan is not None:
        if body.plan not in _VALID_PLANS:
            raise HTTPException(status_code=400, detail=f"Plan inválido: {body.plan}")
        user.plan = body.plan
        # Si pasa a un plan de research, recarga el saldo de escaneos del mes
        research_def = stripe_service.RESEARCH_PLAN_DEFS.get(body.plan)
        if research_def is not None:
            user.scans_remaining = research_def["scans_per_month"]

    if body.subscription_status is not None:
        if body.subscription_status not in _VALID_STATUSES:
            raise HTTPException(
                status_code=400, detail=f"Estado inválido: {body.subscription_status}"
            )
        user.subscription_status = body.subscription_status

    if body.is_founder is not None:
        user.is_founder = body.is_founder

    await db.commit()
    await db.refresh(user)

    closer_name = None
    if user.closer_id is not None:
        closer = await db.get(Closer, user.closer_id)
        closer_name = closer.full_name if closer else None
    return _client_row(user, closer_name)


# ── Closers ───────────────────────────────────────────────────────────────────
async def _closer_totals(db: AsyncSession, closer_id: uuid.UUID) -> tuple[int, int, int]:
    """(clients_count, pending_cents, paid_cents) de un closer."""
    clients = int(
        (await db.execute(select(func.count(User.id)).where(User.closer_id == closer_id))).scalar()
        or 0
    )
    pending = (
        await db.execute(
            select(func.coalesce(func.sum(Commission.commission_amount), 0)).where(
                Commission.closer_id == closer_id,
                Commission.status == COMMISSION_PENDING,
            )
        )
    ).scalar()
    paid = (
        await db.execute(
            select(func.coalesce(func.sum(Commission.commission_amount), 0)).where(
                Commission.closer_id == closer_id,
                Commission.status == COMMISSION_PAID,
            )
        )
    ).scalar()
    return clients, _cents(pending), _cents(paid)


def _closer_row(closer: Closer, clients: int, pending: int, paid: int) -> CloserRow:
    return CloserRow(
        id=closer.id,
        full_name=closer.full_name,
        email=closer.email,
        phone=closer.phone,
        commission_rate=closer.commission_rate,
        referral_code=closer.referral_code,
        is_active=closer.is_active,
        clients_count=clients,
        commissions_pending_cents=pending,
        commissions_paid_cents=paid,
        created_at=closer.created_at,
    )


@router.get("/closers", response_model=list[CloserRow])
async def list_closers(db: AsyncSession = Depends(get_db)) -> list[CloserRow]:
    result = await db.execute(select(Closer).order_by(Closer.created_at.desc()))
    closers = list(result.scalars())
    rows: list[CloserRow] = []
    for c in closers:
        clients, pending, paid = await _closer_totals(db, c.id)
        rows.append(_closer_row(c, clients, pending, paid))
    return rows


@router.post("/closers", response_model=CloserCreated, status_code=201)
async def create_closer(body: CloserCreate, db: AsyncSession = Depends(get_db)) -> CloserCreated:
    existing = await db.execute(select(Closer.id).where(Closer.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Ya existe un closer con ese email")

    temp_password = body.password or secrets.token_urlsafe(9)
    closer = Closer(
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        commission_rate=body.commission_rate,
        referral_code=await generate_referral_code(db),
        is_active=True,
        hashed_password=hash_password(temp_password),
    )
    db.add(closer)
    await db.commit()
    await db.refresh(closer)
    row = _closer_row(closer, 0, 0, 0)
    return CloserCreated(**row.model_dump(), temp_password=temp_password)


@router.post("/closers/{closer_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_closer_password(
    closer_id: uuid.UUID, db: AsyncSession = Depends(get_db)
) -> ResetPasswordResponse:
    closer = await db.get(Closer, closer_id)
    if not closer:
        raise HTTPException(status_code=404, detail="Closer no encontrado")
    temp_password = secrets.token_urlsafe(9)
    closer.hashed_password = hash_password(temp_password)
    await db.commit()
    return ResetPasswordResponse(temp_password=temp_password)


@router.get("/closers/{closer_id}", response_model=CloserDetail)
async def closer_detail(closer_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> CloserDetail:
    closer = await db.get(Closer, closer_id)
    if not closer:
        raise HTTPException(status_code=404, detail="Closer no encontrado")

    clients_res = await db.execute(
        select(User).where(User.closer_id == closer_id).order_by(User.created_at.desc())
    )
    clients = [
        AdminClientRow(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            plan=u.plan,
            subscription_status=u.subscription_status,
            is_founder=u.is_founder,
            closer_id=u.closer_id,
            closer_name=closer.full_name,
            mrr_cents=_user_mrr_cents(u),
            created_at=u.created_at,
        )
        for u in clients_res.scalars()
    ]

    comm_res = await db.execute(
        select(Commission).where(Commission.closer_id == closer_id).order_by(
            Commission.created_at.desc()
        )
    )
    emails = {
        u.id: u.email
        for u in (await db.execute(select(User).where(User.closer_id == closer_id))).scalars()
    }
    commissions = [
        _commission_row(c, closer.full_name, emails.get(c.user_id)) for c in comm_res.scalars()
    ]

    clients_count, pending, paid = await _closer_totals(db, closer_id)
    return CloserDetail(
        closer=_closer_row(closer, clients_count, pending, paid),
        clients=clients,
        commissions=commissions,
    )


@router.patch("/closers/{closer_id}", response_model=CloserRow)
async def update_closer(
    closer_id: uuid.UUID, body: CloserUpdate, db: AsyncSession = Depends(get_db)
) -> CloserRow:
    closer = await db.get(Closer, closer_id)
    if not closer:
        raise HTTPException(status_code=404, detail="Closer no encontrado")

    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(closer, field, value)
    await db.commit()
    await db.refresh(closer)
    clients, pending, paid = await _closer_totals(db, closer_id)
    return _closer_row(closer, clients, pending, paid)


# ── Comisiones ────────────────────────────────────────────────────────────────
def _commission_row(c: Commission, closer_name: str | None, client_email: str | None) -> CommissionRow:
    return CommissionRow(
        id=c.id,
        closer_id=c.closer_id,
        closer_name=closer_name,
        user_id=c.user_id,
        client_email=client_email,
        stripe_invoice_id=c.stripe_invoice_id,
        type=c.type,
        base_amount=c.base_amount,
        commission_amount=c.commission_amount,
        currency=c.currency,
        period_start=c.period_start,
        status=c.status,
        paid_at=c.paid_at,
        created_at=c.created_at,
    )


@router.get("/commissions", response_model=list[CommissionRow])
async def list_commissions(
    db: AsyncSession = Depends(get_db),
    closer_id: uuid.UUID | None = Query(default=None),
    status: str | None = Query(default=None),
) -> list[CommissionRow]:
    stmt = select(Commission).order_by(Commission.created_at.desc())
    if closer_id:
        stmt = stmt.where(Commission.closer_id == closer_id)
    if status:
        stmt = stmt.where(Commission.status == status)
    comms = list((await db.execute(stmt)).scalars())

    closer_names = await _closer_name_map(db)
    user_ids = {c.user_id for c in comms}
    emails: dict[uuid.UUID, str] = {}
    if user_ids:
        rows = (await db.execute(select(User.id, User.email).where(User.id.in_(user_ids)))).all()
        emails = {r[0]: r[1] for r in rows}

    return [
        _commission_row(c, closer_names.get(c.closer_id), emails.get(c.user_id)) for c in comms
    ]


# ── Costes API (OpenAI) ────────────────────────────────────────────────────────

from datetime import date

# Estimación de tokens por agente (basado en data histórica)
_AGENT_TOKEN_ESTIMATES = {
    "ResearchAgent": {"prompt": 2000, "completion": 3000},      # búsqueda + análisis
    "CopyAgent": {"prompt": 5000, "completion": 4000},           # 5 variantes
    "LandingAgent": {"prompt": 4000, "completion": 3500},        # contenido A/B
    "AdsAgent": {"prompt": 3000, "completion": 2500},            # JSON campaign
    "LeadMagnetAgent": {"prompt": 2000, "completion": 2000},     # PDF structure
    "EmailAgent": {"prompt": 3000, "completion": 2500},          # 5 emails + WA + thanks
    "MetaPolicyAgent": {"prompt": 1500, "completion": 1000},     # validación
}


class ApiCostsResponse(BaseModel):
    month: str                              # ej: "2026-05"
    total_plans_executed: int
    estimated_total_tokens: int
    estimated_cost_usd: float
    by_agent: dict[str, dict]              # agent_name → {tokens, cost}


@router.get("/api-costs", response_model=ApiCostsResponse)
async def get_api_costs(
    db: AsyncSession = Depends(get_db),
    month: str | None = Query(default=None),  # ej: "2026-05", default es este mes
) -> ApiCostsResponse:
    """Costes reales de OpenAI del mes actual.

    Lee de la tabla ApiUsage los tokens consumidos por agente.
    """
    if not month:
        today = date.today()
        month = f"{today.year:04d}-{today.month:02d}"

    # Fecha range para el mes
    year, month_num = int(month[:4]), int(month[5:7])
    start = datetime(year, month_num, 1, tzinfo=timezone.utc)
    next_month = month_num + 1 if month_num < 12 else 1
    next_year = year if month_num < 12 else year + 1
    end = datetime(next_year, next_month, 1, tzinfo=timezone.utc)

    from app.models.api_usage import ApiUsage

    # Leer uso real de la tabla ApiUsage
    result = await db.execute(
        select(ApiUsage).where(
            ApiUsage.created_at >= start,
            ApiUsage.created_at < end,
        ).order_by(ApiUsage.created_at.desc())
    )
    usages = list(result.scalars())

    # Contar planes únicos ejecutados
    plan_ids = {u.plan_id for u in usages if u.plan_id}
    total_plans = len(plan_ids)

    # Agrupar por agente
    by_agent: dict[str, dict] = {}
    total_tokens = 0
    total_cost = 0.0

    for usage in usages:
        agent = usage.agent_name
        if agent not in by_agent:
            by_agent[agent] = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cost_usd": 0.0,
            }
        by_agent[agent]["prompt_tokens"] += usage.prompt_tokens
        by_agent[agent]["completion_tokens"] += usage.completion_tokens
        by_agent[agent]["cost_usd"] += float(usage.cost_usd)
        total_tokens += usage.prompt_tokens + usage.completion_tokens
        total_cost += float(usage.cost_usd)

    # Redondear costes
    for agent_data in by_agent.values():
        agent_data["cost_usd"] = round(agent_data["cost_usd"], 4)

    return ApiCostsResponse(
        month=month,
        total_plans_executed=total_plans,
        estimated_total_tokens=total_tokens,
        estimated_cost_usd=round(total_cost, 4),
        by_agent=by_agent,
    )


def _calculate_openai_cost(prompt_tokens: int, completion_tokens: int) -> float:
    """Calcula coste en USD (gpt-4o: $5/1M input, $15/1M output)."""
    input_cost = (prompt_tokens / 1_000_000) * 5.00
    output_cost = (completion_tokens / 1_000_000) * 15.00
    return input_cost + output_cost


@router.post("/commissions/liquidate", response_model=LiquidateResponse)
async def liquidate_commissions(
    body: LiquidateRequest, db: AsyncSession = Depends(get_db)
) -> LiquidateResponse:
    result = await db.execute(
        select(Commission).where(
            Commission.id.in_(body.commission_ids),
            Commission.status == COMMISSION_PENDING,
        )
    )
    comms = list(result.scalars())
    now = datetime.now(timezone.utc)
    total = Decimal("0")
    for c in comms:
        c.status = COMMISSION_PAID
        c.paid_at = now
        total += Decimal(c.commission_amount)
    await db.commit()
    return LiquidateResponse(liquidated=len(comms), total_cents=_cents(total))
