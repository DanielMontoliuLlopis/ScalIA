from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.auth import get_active_client_account, get_current_user
from app.database import get_db
from app.models.client_account import ClientAccount
from app.models.user import User
from app.models.user_settings import UserSettings
from app.services import permissions
from app.schemas.settings import UserSettingsResponse, UserSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


def _to_response(settings: UserSettings) -> UserSettingsResponse:
    return UserSettingsResponse(
        id=settings.id,
        user_id=settings.user_id,
        client_account_id=settings.client_account_id,
        meta_pixel_id=settings.meta_pixel_id,
        meta_ad_account_id=settings.meta_ad_account_id,
        color_palette=settings.color_palette,
        logo_url=settings.logo_url,
        company_name=settings.company_name,
        business_description=settings.business_description,
        business_type=settings.business_type,
        resend_from_email=settings.resend_from_email,
        privacy_policy_url=settings.privacy_policy_url,
        has_resend_key=bool(settings.resend_api_key),
        has_meta_token=bool(settings.meta_access_token),
        whatsapp_phone_number_id=settings.whatsapp_phone_number_id,
        whatsapp_phone_display=settings.whatsapp_phone_display,
        created_at=settings.created_at,
        updated_at=settings.updated_at,
    )


@router.get("", response_model=UserSettingsResponse)
async def get_settings(
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> UserSettingsResponse:
    result = await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account.id)
    )
    settings = result.scalar_one_or_none()
    if not settings:
        settings = UserSettings(client_account_id=client_account.id, user_id=current_user.id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    return _to_response(settings)


@router.get("/completeness")
async def get_completeness(
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account.id)
    )
    s = result.scalar_one_or_none()
    missing = []
    if not s or not s.company_name:
        missing.append("company_name")
    if not s or not s.business_description:
        missing.append("business_description")
    if not s or not s.business_type:
        missing.append("business_type")
    return {"complete": len(missing) == 0, "missing": missing}


@router.put("", response_model=UserSettingsResponse)
async def update_settings(
    body: UserSettingsUpdate,
    current_user: User = Depends(permissions.require_action("edit_settings")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> UserSettingsResponse:
    changes = body.model_dump(exclude_none=True)

    # WhatsApp es feature de tier Starter+: bloquear si intenta configurarlo sin el feature
    whatsapp_fields = {"whatsapp_phone_number_id", "whatsapp_phone_display"}
    if whatsapp_fields & changes.keys() and not permissions.has_feature(current_user, "whatsapp"):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Tu plan ({permissions.tier_of(current_user)}) no incluye WhatsApp. "
                f"Mejora a Starter o superior."
            ),
        )

    result = await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account.id)
    )
    settings = result.scalar_one_or_none()
    if not settings:
        settings = UserSettings(client_account_id=client_account.id, user_id=current_user.id)
        db.add(settings)

    for field, value in changes.items():
        setattr(settings, field, value)

    await db.commit()
    await db.refresh(settings)
    return _to_response(settings)


@router.post("/meta/create-pixel")
async def create_meta_pixel(
    current_user: User = Depends(permissions.require_action("edit_settings")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> dict:
    result = await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account.id)
    )
    settings = result.scalar_one_or_none()
    if not settings or not settings.meta_access_token:
        raise HTTPException(status_code=400, detail="Meta no conectado")
    if not settings.meta_ad_account_id:
        raise HTTPException(status_code=400, detail="Selecciona una cuenta publicitaria primero")

    pixel_name = f"{settings.company_name or 'Growth OS'} Pixel"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"https://graph.facebook.com/v23.0/{settings.meta_ad_account_id}/adspixels",
            params={
                "name": pixel_name,
                "access_token": settings.meta_access_token,
            },
        )
    data = resp.json()
    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"].get("message", "Error Meta API"))

    pixel_id = str(data["id"])
    settings.meta_pixel_id = pixel_id
    await db.commit()
    return {"pixel_id": pixel_id}
