import asyncio
import json

import redis.asyncio as aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings as app_settings
from app.pubsub import CHANNEL_PREFIX
from app.routers import auth, analytics, billing, plans, landings, campaigns, leads, uploads, recommendations, team, admin, closer_portal, client_accounts, lead_forms
from app.routers import settings as settings_router
from app.routers import meta_oauth
from app.services import stripe_service
from app.ws import manager

app = FastAPI(title="Growth OS", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(plans.router)
app.include_router(settings_router.router)
app.include_router(landings.router)
app.include_router(campaigns.router)
app.include_router(leads.router)
app.include_router(meta_oauth.router)
app.include_router(billing.router)
app.include_router(uploads.router)
app.include_router(analytics.router)
app.include_router(recommendations.router)
app.include_router(team.router)
app.include_router(admin.router)
app.include_router(closer_portal.router)
app.include_router(client_accounts.router)
app.include_router(lead_forms.router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str) -> None:
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)


async def _redis_subscriber() -> None:
    """Escucha todos los canales ws:user:* en Redis y reenvía al WebSocket correspondiente."""
    while True:
        try:
            r = aioredis.from_url(app_settings.REDIS_URL)
            pubsub = r.pubsub()
            await pubsub.psubscribe(f"{CHANNEL_PREFIX}*")
            async for message in pubsub.listen():
                if message["type"] != "pmessage":
                    continue
                try:
                    channel: str = message["channel"].decode()
                    user_id = channel.removeprefix(CHANNEL_PREFIX)
                    data = json.loads(message["data"])
                    await manager.broadcast(user_id, data)
                except Exception:
                    pass
        except Exception:
            await asyncio.sleep(2)


@app.on_event("startup")
async def startup() -> None:
    asyncio.create_task(_redis_subscriber())
    try:
        await asyncio.to_thread(stripe_service.ensure_products_and_prices)
    except Exception:
        import logging
        logging.exception("Error inicializando productos Stripe")
