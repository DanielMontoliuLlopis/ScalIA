import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_active_client_account, get_current_user
from app.database import get_db
from app.models.client_account import ClientAccount
from app.models.lead_form import LeadForm
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.lead_form import LeadFormCreate, LeadFormResponse, LeadFormUpdate
from app.tools.meta_ads import MetaAdsError, create_leadgen_form

router = APIRouter(prefix="/lead-forms", tags=["lead-forms"])


async def _get_form(db: AsyncSession, form_id: uuid.UUID, account_id: uuid.UUID) -> LeadForm:
    form = (
        await db.execute(
            select(LeadForm).where(
                LeadForm.id == form_id, LeadForm.client_account_id == account_id
            )
        )
    ).scalar_one_or_none()
    if not form:
        raise HTTPException(status_code=404, detail="Formulario no encontrado")
    return form


def _to_def(form: LeadForm) -> dict:
    return {
        "name": form.name,
        "locale": form.locale,
        "intro_headline": form.intro_headline,
        "intro_description": form.intro_description,
        "fields": form.fields or [],
        "privacy_policy_url": form.privacy_policy_url,
        "privacy_policy_link_text": form.privacy_policy_link_text,
        "thank_you_title": form.thank_you_title,
        "thank_you_body": form.thank_you_body,
        "thank_you_button_text": form.thank_you_button_text,
        "thank_you_button_type": form.thank_you_button_type,
        "thank_you_website_url": form.thank_you_website_url,
    }


@router.get("", response_model=list[LeadFormResponse])
async def list_forms(
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[LeadForm]:
    result = await db.execute(
        select(LeadForm)
        .where(LeadForm.client_account_id == client_account.id)
        .order_by(LeadForm.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=LeadFormResponse, status_code=201)
async def create_form(
    body: LeadFormCreate,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> LeadForm:
    form = LeadForm(
        client_account_id=client_account.id,
        user_id=current_user.id,
        **body.model_dump(),
    )
    # fields llega como lista de modelos pydantic → dicts
    form.fields = [f.model_dump() if hasattr(f, "model_dump") else f for f in (body.fields or [])]
    db.add(form)
    await db.commit()
    await db.refresh(form)
    return form


@router.get("/{form_id}", response_model=LeadFormResponse)
async def get_form(
    form_id: uuid.UUID,
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> LeadForm:
    return await _get_form(db, form_id, client_account.id)


@router.patch("/{form_id}", response_model=LeadFormResponse)
async def update_form(
    form_id: uuid.UUID,
    body: LeadFormUpdate,
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> LeadForm:
    form = await _get_form(db, form_id, client_account.id)
    data = body.model_dump(exclude_unset=True)
    if "fields" in data and data["fields"] is not None:
        data["fields"] = [
            f.model_dump() if hasattr(f, "model_dump") else f for f in body.fields
        ]
    for key, value in data.items():
        setattr(form, key, value)
    # Editar invalida la sincronización: los forms de Meta son inmutables → re-sync crea uno nuevo
    form.meta_form_id = None
    form.meta_page_id = None
    form.synced_at = None
    await db.commit()
    await db.refresh(form)
    return form


@router.delete("/{form_id}", status_code=204)
async def delete_form(
    form_id: uuid.UUID,
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> None:
    form = await _get_form(db, form_id, client_account.id)
    await db.delete(form)
    await db.commit()


@router.post("/{form_id}/sync-meta", response_model=LeadFormResponse)
async def sync_meta(
    form_id: uuid.UUID,
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> LeadForm:
    form = await _get_form(db, form_id, client_account.id)
    settings = (
        await db.execute(
            select(UserSettings).where(UserSettings.client_account_id == client_account.id)
        )
    ).scalar_one_or_none()
    if not settings or not settings.meta_access_token or not settings.meta_page_id:
        raise HTTPException(
            status_code=400,
            detail="Conecta tu página de Meta (token + Page ID) en Ajustes antes de sincronizar.",
        )
    if not form.privacy_policy_url:
        raise HTTPException(
            status_code=400,
            detail="El formulario necesita una URL de política de privacidad para crearse en Meta.",
        )
    try:
        meta_form_id = await create_leadgen_form(
            settings.meta_access_token, settings.meta_page_id, _to_def(form)
        )
    except MetaAdsError as e:
        raise HTTPException(status_code=422, detail=f"Error Meta API: {e}")
    form.meta_form_id = meta_form_id
    form.meta_page_id = settings.meta_page_id
    form.synced_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(form)
    return form
