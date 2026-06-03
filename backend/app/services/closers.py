"""Helpers de closers: generación de referral_code y resolución de atribución."""
from __future__ import annotations

import secrets
import string

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.closer import Closer

_ALPHABET = string.ascii_lowercase + string.digits


async def generate_referral_code(db: AsyncSession, length: int = 8) -> str:
    """Genera un referral_code único (no colisiona con los existentes)."""
    for _ in range(20):
        code = "".join(secrets.choice(_ALPHABET) for _ in range(length))
        exists = await db.execute(select(Closer.id).where(Closer.referral_code == code))
        if not exists.scalar_one_or_none():
            return code
    # Fallback extremadamente improbable
    return "".join(secrets.choice(_ALPHABET) for _ in range(length + 4))


async def closer_by_ref_code(db: AsyncSession, code: str | None) -> Closer | None:
    """Devuelve el closer activo cuyo referral_code coincide, o None."""
    if not code:
        return None
    result = await db.execute(
        select(Closer).where(
            Closer.referral_code == code.strip().lower(),
            Closer.is_active.is_(True),
        )
    )
    return result.scalar_one_or_none()
