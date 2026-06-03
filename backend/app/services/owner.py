"""Owner / superadmin bypass.

Emails listados en OWNER_EMAILS reciben automáticamente:
- plan = agency (tier más alto)
- role = owner
- subscription_status = active
- active_campaigns_limit = ilimitado
- Sin necesidad de pasar por Stripe Checkout.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User


def is_owner(email: str | None) -> bool:
    if not email:
        return False
    owners = {e.strip().lower() for e in settings.OWNER_EMAILS.split(",") if e.strip()}
    return email.lower() in owners


def apply_owner_overrides(user: User) -> None:
    """Aplica privilegios de owner al objeto User (sin commit)."""
    user.plan = "agency"
    user.role = "owner"
    user.is_superadmin = True
    user.subscription_status = "active"
    user.active_campaigns_limit = 9999
    if not user.subscription_current_period_end:
        user.subscription_current_period_end = datetime.now(timezone.utc) + timedelta(days=3650)


async def ensure_owners(db: AsyncSession) -> None:
    """Refresca privilegios de owner en todos los usuarios cuyo email esté en OWNER_EMAILS."""
    owner_emails = [e.strip().lower() for e in settings.OWNER_EMAILS.split(",") if e.strip()]
    if not owner_emails:
        return
    result = await db.execute(select(User).where(User.email.in_(owner_emails)))
    for user in result.scalars():
        apply_owner_overrides(user)
    await db.commit()
