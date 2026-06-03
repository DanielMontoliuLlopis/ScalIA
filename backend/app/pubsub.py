import json

import redis as redis_sync
import redis.asyncio as aioredis

from app.config import settings

CHANNEL_PREFIX = "ws:user:"


def publish_event(user_id: str, data: dict) -> None:
    """Síncrono — usado desde Celery worker."""
    r = redis_sync.from_url(settings.REDIS_URL)
    channel = f"{CHANNEL_PREFIX}{user_id}"
    r.publish(channel, json.dumps(data))
    r.close()


async def async_publish_event(user_id: str, data: dict) -> None:
    """Asíncrono — usado desde FastAPI routers."""
    r = aioredis.from_url(settings.REDIS_URL)
    channel = f"{CHANNEL_PREFIX}{user_id}"
    await r.publish(channel, json.dumps(data))
    await r.aclose()
