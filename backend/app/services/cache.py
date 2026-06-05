"""Caché JSON en Redis para respuestas costosas (insights Meta en vivo).

Degrada con elegancia: si Redis falla, get devuelve None y set es no-op —
la app sigue funcionando pegando a la fuente original.
"""
import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "cache:"


async def cache_get(key: str) -> Any | None:
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        raw = await r.get(f"{_CACHE_PREFIX}{key}")
        await r.aclose()
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.warning("cache_get failed (%s): %s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl_seconds: int = 900) -> None:
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        await r.set(f"{_CACHE_PREFIX}{key}", json.dumps(value), ex=ttl_seconds)
        await r.aclose()
    except Exception as exc:
        logger.warning("cache_set failed (%s): %s", key, exc)
