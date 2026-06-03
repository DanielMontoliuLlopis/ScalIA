import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_active_client_account, get_current_user
from app.config import settings
from app.database import get_db
from app.models.client_account import ClientAccount
from app.models.user import User
from app.models.user_settings import UserSettings

router = APIRouter(prefix="/meta", tags=["meta"])

META_GRAPH = "https://graph.facebook.com/v19.0"
META_OAUTH = "https://www.facebook.com/v19.0/dialog/oauth"
META_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"

SCOPES = "ads_management,ads_read,pages_read_engagement,pages_show_list,business_management"


def _callback_url() -> str:
    return f"{settings.FRONTEND_URL}/meta/callback"


@router.get("/connect-url")
async def get_connect_url(
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
) -> dict:
    """Devuelve la URL de OAuth de Meta para redirigir al usuario.

    El `state` lleva user_id:client_account_id para saber a qué workspace
    asociar el token en el callback (que no tiene header de contexto).
    """
    if not settings.META_APP_ID:
        raise HTTPException(status_code=500, detail="META_APP_ID no configurado en el servidor")

    state = f"{current_user.id}:{client_account.id}"
    url = (
        f"{META_OAUTH}"
        f"?client_id={settings.META_APP_ID}"
        f"&redirect_uri={_callback_url()}"
        f"&scope={SCOPES}"
        f"&state={state}"
        f"&response_type=code"
    )
    return {"url": url}


@router.post("/exchange")
async def handle_callback(
    body: dict,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Recibe el code de OAuth, lo intercambia por un token de larga duración y lo guarda.
    Usa el user_id del campo state (enviado por Meta de vuelta) para identificar al usuario sin JWT."""
    code = body.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Falta el parámetro code")

    state = body.get("state")
    if not state:
        raise HTTPException(status_code=400, detail="Falta el parámetro state")
    # state = "user_id:client_account_id" (formato nuevo) o "user_id" (legado)
    if ":" in state:
        user_id, client_account_id = state.split(":", 1)
    else:
        user_id, client_account_id = state, None

    # Intercambiar code por short-lived token
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(META_TOKEN_URL, params={
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "redirect_uri": _callback_url(),
            "code": code,
        })
    data = resp.json()
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"].get("message", "Error OAuth Meta"))

    short_token = data.get("access_token")
    if not short_token:
        raise HTTPException(status_code=400, detail="No se recibió access_token de Meta")

    # Intercambiar por long-lived token (60 días)
    async with httpx.AsyncClient(timeout=15) as client:
        long_resp = await client.get(META_TOKEN_URL, params={
            "grant_type": "fb_exchange_token",
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "fb_exchange_token": short_token,
        })
    long_data = long_resp.json()
    long_token = long_data.get("access_token", short_token)

    # Resolver el workspace destino. Si el state no lo trae (legado), usar el
    # primer client_account del owner del usuario.
    if not client_account_id:
        ca_res = await db.execute(
            select(ClientAccount)
            .where(ClientAccount.owner_id == user_id)
            .order_by(ClientAccount.created_at.asc())
            .limit(1)
        )
        ca = ca_res.scalar_one_or_none()
        if not ca:
            raise HTTPException(status_code=404, detail="No se encontró workspace para el usuario")
        client_account_id = str(ca.id)

    # Guardar en UserSettings del workspace
    result = await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account_id)
    )
    user_settings = result.scalar_one_or_none()
    if not user_settings:
        user_settings = UserSettings(client_account_id=client_account_id, user_id=user_id)
        db.add(user_settings)

    user_settings.meta_access_token = long_token
    await db.commit()

    return {"success": True, "message": "Cuenta Meta conectada correctamente"}


@router.get("/ad-accounts")
async def list_ad_accounts(
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista las cuentas publicitarias disponibles para el token del workspace."""
    result = await db.execute(select(UserSettings).where(UserSettings.client_account_id == client_account.id))
    user_settings = result.scalar_one_or_none()

    if not user_settings or not user_settings.meta_access_token:
        raise HTTPException(status_code=400, detail="Cuenta Meta no conectada")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{META_GRAPH}/me/adaccounts",
            params={
                "access_token": user_settings.meta_access_token,
                "fields": "id,name,account_status,currency,timezone_name",
                "limit": 50,
            },
        )
    data = resp.json()
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"].get("message", "Error Meta API"))

    return {"ad_accounts": data.get("data", [])}


@router.post("/select-account")
async def select_ad_account(
    body: dict,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Guarda el Ad Account ID y opcionalmente el Pixel ID elegido por el usuario."""
    ad_account_id = body.get("ad_account_id")
    if not ad_account_id:
        raise HTTPException(status_code=400, detail="Falta ad_account_id")

    result = await db.execute(select(UserSettings).where(UserSettings.client_account_id == client_account.id))
    user_settings = result.scalar_one_or_none()
    if not user_settings:
        user_settings = UserSettings(client_account_id=client_account.id, user_id=current_user.id)
        db.add(user_settings)

    # Normalizar formato act_XXXXX
    if not ad_account_id.startswith("act_"):
        ad_account_id = f"act_{ad_account_id}"

    user_settings.meta_ad_account_id = ad_account_id
    if body.get("meta_pixel_id"):
        user_settings.meta_pixel_id = body["meta_pixel_id"]

    await db.commit()
    return {"success": True, "ad_account_id": ad_account_id}


@router.get("/pages")
async def list_pages(
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista las Facebook Pages del usuario para seleccionar la que usará en los ads."""
    result = await db.execute(select(UserSettings).where(UserSettings.client_account_id == client_account.id))
    user_settings = result.scalar_one_or_none()

    if not user_settings or not user_settings.meta_access_token:
        raise HTTPException(status_code=400, detail="Cuenta Meta no conectada")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(
            f"{META_GRAPH}/me/accounts",
            params={
                "access_token": user_settings.meta_access_token,
                "fields": "id,name,category,fan_count",
            },
        )
    data = resp.json()
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"].get("message", "Error Meta API"))

    return {"pages": data.get("data", [])}


@router.post("/select-page")
async def select_page(
    body: dict,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Guarda el Page ID elegido para usar en los creativos de ads."""
    page_id = body.get("page_id")
    if not page_id:
        raise HTTPException(status_code=400, detail="Falta page_id")

    result = await db.execute(select(UserSettings).where(UserSettings.client_account_id == client_account.id))
    user_settings = result.scalar_one_or_none()
    if not user_settings:
        user_settings = UserSettings(client_account_id=client_account.id, user_id=current_user.id)
        db.add(user_settings)

    user_settings.meta_page_id = page_id
    await db.commit()
    return {"success": True, "page_id": page_id}


@router.delete("/disconnect")
async def disconnect_meta(
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Desconecta la cuenta de Meta eliminando el token y las keys."""
    result = await db.execute(select(UserSettings).where(UserSettings.client_account_id == client_account.id))
    user_settings = result.scalar_one_or_none()
    if user_settings:
        user_settings.meta_access_token = None
        user_settings.meta_ad_account_id = None
        user_settings.meta_pixel_id = None
        user_settings.meta_page_id = None
        await db.commit()
    return {"success": True}
