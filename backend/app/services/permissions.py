"""Permisos y limitaciones de la app.

Dos ejes de control de acceso:

1. TIER (plan de suscripción)  → qué FEATURES y qué LÍMITES tiene la cuenta.
   Plataforma completa: trial | starter | growth | agency
   Research Mode (solo research + ángulos, sin funnel): research_10 | research_100

2. ROL de equipo (dentro de una cuenta) → qué ACCIONES puede hacer el usuario.
   owner | admin | member | viewer

Reglas deterministas, sin LLM. Se usan como dependencias FastAPI.
"""
from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.database import get_db
from app.models.plan import Plan, PlanStatus
from app.models.user import User

# ─────────────────────────────────────────────────────────────────────────────
# 1. TIERS — features y límites por plan
# ─────────────────────────────────────────────────────────────────────────────

# Features disponibles por tier. El núcleo (copies, landing, leads, emails, crm)
# está en todos los tiers de pago. Los extras se desbloquean por tier.
TIER_FEATURES: dict[str, set[str]] = {
    # Sin suscripción activa (nuevo sin pagar / cancelado): cero acceso.
    "canceled": set(),
    "trial": {
        "campaigns", "copy", "landing", "leads", "crm",
    },
    "starter": {
        "campaigns", "copy", "landing", "leads", "crm",
        "email_sequences", "whatsapp", "lead_magnet",
        "multi_angle", "optimization", "angle_history", "research_export",
    },
    "growth": {
        "campaigns", "copy", "landing", "leads", "crm",
        "email_sequences", "whatsapp", "lead_magnet",
        "offer_testing", "team", "optimization",
        "multi_angle", "angle_history", "research_export",
    },
    "agency": {
        "campaigns", "copy", "landing", "leads", "crm",
        "email_sequences", "whatsapp", "lead_magnet",
        "offer_testing", "team", "optimization",
        "multi_meta_account", "white_label", "priority_support",
        "multi_angle", "research_export", "angle_history",
    },
    # Research Mode — solo research + 6 ángulos, sin funnel/campañas/ads.
    "research_10": {
        "research_only", "research_export", "angle_history",
    },
    "research_100": {
        "research_only", "research_export", "angle_history",
    },
}

# Límites numéricos por tier. scans_per_month = tope de escaneos de research/mes
# (1 escaneo = 1 generación de research). Se reinicia cada ciclo, no acumula.
TIER_LIMITS: dict[str, dict[str, int]] = {
    "canceled":     {"active_campaigns": 0, "team_seats": 0, "client_accounts": 0, "scans_per_month": 0},
    "trial":        {"active_campaigns": 1, "team_seats": 1, "client_accounts": 1, "scans_per_month": 1},
    "starter":      {"active_campaigns": 1, "team_seats": 1, "client_accounts": 1, "scans_per_month": 10},
    "growth":       {"active_campaigns": 5, "team_seats": 3, "client_accounts": 1, "scans_per_month": 30},
    "agency":       {"active_campaigns": 30, "team_seats": 9999, "client_accounts": 9999, "scans_per_month": 100},
    # Research Mode — sin campañas; solo escaneos de research.
    "research_10":  {"active_campaigns": 0, "team_seats": 1, "client_accounts": 1, "scans_per_month": 10},
    "research_100": {"active_campaigns": 0, "team_seats": 1, "client_accounts": 1, "scans_per_month": 100},
}

# Precio mensual de los planes Research Mode (EUR).
RESEARCH_PLAN_PRICE_EUR: dict[str, int] = {
    "research_10": 15,
    "research_100": 99,
}


def tier_of(user: User) -> str:
    # Sin suscripción activa → "canceled" (cero acceso). No hay trial gratuito.
    return user.plan if user.plan in TIER_FEATURES else "canceled"


def has_feature(user: User, feature: str) -> bool:
    return feature in TIER_FEATURES.get(tier_of(user), set())


def tier_limit(user: User, key: str) -> int:
    return TIER_LIMITS.get(tier_of(user), TIER_LIMITS["canceled"]).get(key, 0)


def is_research_only(user: User) -> bool:
    """True si el plan es Research Mode (sin funnel/campañas/ads)."""
    return has_feature(user, "research_only")


def scans_per_month(user: User) -> int:
    """Tope de escaneos de research/mes del plan (se reinicia cada ciclo)."""
    return tier_limit(user, "scans_per_month")


def _maybe_reset_scans(user: User) -> None:
    """Reinicia el saldo de escaneos al tope si comenzó un nuevo ciclo.
    El saldo NO acumula: al reiniciar se fija al tope del plan."""
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    cap = scans_per_month(user)
    if user.scans_reset_at is None or user.scans_reset_at <= now:
        user.scans_remaining = cap
        # Próximo reinicio: fin del periodo de suscripción si existe, si no +30 días
        nxt = user.subscription_current_period_end
        if nxt is None or nxt <= now:
            nxt = now + timedelta(days=30)
        user.scans_reset_at = nxt


async def consume_scan(db: AsyncSession, user: User) -> int:
    """Descuenta 1 escaneo del saldo. Reinicia primero si toca. Lanza 402 si no hay saldo.
    Devuelve el saldo restante."""
    _maybe_reset_scans(user)
    if user.scans_remaining <= 0:
        raise HTTPException(
            status_code=402,
            detail=(
                "Sin escaneos restantes este ciclo. Mejora a research_100 o espera al reinicio."
            ),
        )
    user.scans_remaining -= 1
    await db.flush()
    return user.scans_remaining


async def consume_scans(db: AsyncSession, user: User, n: int) -> int:
    """Descuenta `n` escaneos de golpe (atómico). Reinicia primero si toca.
    Lanza 402 si no hay saldo suficiente. Devuelve el saldo restante."""
    n = max(1, n)
    _maybe_reset_scans(user)
    if user.scans_remaining < n:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Necesitas {n} escaneos y te quedan {user.scans_remaining}. "
                "Mejora a research_100 o espera al reinicio."
            ),
        )
    user.scans_remaining -= n
    await db.flush()
    return user.scans_remaining


def require_feature(feature: str):
    """Dependency: exige que el tier de la cuenta incluya `feature`."""

    async def _dep(current_user: User = Depends(get_current_user)) -> User:
        if not has_feature(current_user, feature):
            raise HTTPException(
                status_code=403,
                detail=f"Tu plan ({tier_of(current_user)}) no incluye '{feature}'. Mejora tu plan.",
            )
        return current_user

    return _dep


# ─────────────────────────────────────────────────────────────────────────────
# 2. ROLES DE EQUIPO — acciones permitidas por rol
# ─────────────────────────────────────────────────────────────────────────────

# Jerarquía: owner > admin > member > viewer
ROLE_LEVEL: dict[str, int] = {"viewer": 0, "member": 1, "admin": 2, "owner": 3}

# Acción → nivel mínimo de rol requerido.
ACTION_MIN_ROLE: dict[str, str] = {
    "view": "viewer",            # ver campañas, leads, métricas
    "create_campaign": "member", # crear/ejecutar campañas
    "publish_campaign": "member",
    "edit_leads": "member",      # actualizar lead_status / closed_value
    "edit_settings": "admin",    # tokens Meta, Resend, WhatsApp, paleta
    "manage_billing": "owner",   # checkout, portal, cambiar plan
    "manage_team": "owner",      # invitar / cambiar rol / quitar miembros
}


def can(user: User, action: str) -> bool:
    needed = ACTION_MIN_ROLE.get(action, "owner")
    return ROLE_LEVEL.get(user.role, 0) >= ROLE_LEVEL.get(needed, 99)


def require_action(action: str):
    """Dependency: exige que el ROL del usuario permita `action`."""

    async def _dep(current_user: User = Depends(get_current_user)) -> User:
        if not can(current_user, action):
            raise HTTPException(
                status_code=403,
                detail=f"Tu rol ({current_user.role}) no permite '{action}'.",
            )
        return current_user

    return _dep


def account_owner_id(user: User) -> uuid.UUID:
    """ID de la cuenta a la que pertenece el usuario (él mismo si es owner)."""
    return user.parent_account_id or user.id


# ─────────────────────────────────────────────────────────────────────────────
# 3. LÍMITES dinámicos (consultan la DB)
# ─────────────────────────────────────────────────────────────────────────────

async def count_active_campaigns(db: AsyncSession, owner_id) -> int:
    """Campañas publicadas (con meta_campaign_id) de toda la cuenta (owner + miembros)."""
    member_ids = (
        select(User.id).where(
            (User.id == owner_id) | (User.parent_account_id == owner_id)
        )
    )
    result = await db.execute(
        select(func.count(Plan.id)).where(
            Plan.user_id.in_(member_ids),
            Plan.meta_campaign_id.isnot(None),
        )
    )
    return int(result.scalar() or 0)


async def assert_can_publish_campaign(db: AsyncSession, user: User) -> None:
    """Lanza 403 si la cuenta ya alcanzó su límite de campañas activas."""
    limit = tier_limit(user, "active_campaigns")
    owner_id = account_owner_id(user)
    current = await count_active_campaigns(db, owner_id)
    if current >= limit:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Límite de campañas activas alcanzado ({current}/{limit}) "
                f"para el plan {tier_of(user)}. Mejora tu plan para publicar más."
            ),
        )


async def count_campaigns_in_use(db: AsyncSession, owner_id) -> int:
    """Campañas que ocupan cupo del tier: todo plan de la cuenta que no esté
    rechazado (publicadas + en progreso + borradores). Se usa para impedir que
    el chat arranque el LLM si la cuenta ya llegó a su límite de campañas."""
    member_ids = (
        select(User.id).where(
            (User.id == owner_id) | (User.parent_account_id == owner_id)
        )
    )
    result = await db.execute(
        select(func.count(Plan.id)).where(
            Plan.user_id.in_(member_ids),
            Plan.status != PlanStatus.rejected.value,
        )
    )
    return int(result.scalar() or 0)


async def assert_can_create_campaign(db: AsyncSession, user: User) -> None:
    """Lanza 403 si la cuenta ya alcanzó su límite de campañas (incluye en progreso)."""
    limit = tier_limit(user, "active_campaigns")
    owner_id = account_owner_id(user)
    current = await count_campaigns_in_use(db, owner_id)
    if current >= limit:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Límite de campañas alcanzado ({current}/{limit}) para el plan "
                f"{tier_of(user)}. Mejora tu plan o archiva una campaña para crear otra."
            ),
        )


async def count_team_members(db: AsyncSession, owner_id) -> int:
    """Total de usuarios en la cuenta (owner + sub-usuarios)."""
    result = await db.execute(
        select(func.count(User.id)).where(
            (User.id == owner_id) | (User.parent_account_id == owner_id)
        )
    )
    return int(result.scalar() or 0)


async def assert_can_add_seat(db: AsyncSession, owner: User) -> None:
    """Lanza 403 si añadir otro miembro supera el límite de asientos del tier."""
    if not has_feature(owner, "team"):
        raise HTTPException(
            status_code=403,
            detail=f"Tu plan ({tier_of(owner)}) no incluye equipo. Mejora a Growth o Agency.",
        )
    limit = tier_limit(owner, "team_seats")
    current = await count_team_members(db, owner.id)
    if current >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Límite de asientos alcanzado ({current}/{limit}) para el plan {tier_of(owner)}.",
        )


async def count_client_accounts(db: AsyncSession, owner_id) -> int:
    """Workspaces (client_accounts) que posee el owner."""
    from app.models.client_account import ClientAccount

    result = await db.execute(
        select(func.count(ClientAccount.id)).where(ClientAccount.owner_id == owner_id)
    )
    return int(result.scalar() or 0)


async def assert_can_create_client_account(db: AsyncSession, user: User) -> None:
    """Lanza 403 si crear otro workspace supera el límite del tier."""
    limit = tier_limit(user, "client_accounts")
    owner_id = account_owner_id(user)
    current = await count_client_accounts(db, owner_id)
    if current >= limit:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Límite de workspaces alcanzado ({current}/{limit}) para el plan "
                f"{tier_of(user)}. Mejora a Agency para gestionar múltiples clientes."
            ),
        )
