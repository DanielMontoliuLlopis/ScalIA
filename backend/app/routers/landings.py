import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_active_client_account, get_current_user
from app.database import get_db
from app.models.client_account import ClientAccount
from app.models.landing_page import LandingPage
from app.models.lead import Lead
from app.models.lead_magnet import LeadMagnet
from app.models.task import AgentTask
from app.models.user import User
from app.services import permissions
from app.schemas.landing import LandingPageResponse, LandingPageUpdate, LeadResponse, LeadSubmit


class ThanksPageData(BaseModel):
    headline: str = "¡Gracias!"
    subheadline: str = "Hemos recibido tus datos. Nos pondremos en contacto contigo pronto."
    next_step_title: str | None = None
    next_step_description: str | None = None
    cta_text: str | None = None
    cta_url: str | None = None
    ps_text: str | None = None
    lead_magnet_url: str | None = None
    lead_magnet_title: str | None = None
    primary_color: str = "#6366f1"
    logo_url: str | None = None

router = APIRouter(tags=["landings"])


@router.get("/plans/{plan_id}/landings", response_model=list[LandingPageResponse])
async def get_plan_landings(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[LandingPage]:
    result = await db.execute(
        select(LandingPage).where(
            LandingPage.plan_id == plan_id,
            LandingPage.client_account_id == client_account.id,
        ).order_by(LandingPage.variant)
    )
    return result.scalars().all()


# Ruta pública — sin auth, accesible desde el exterior
@router.get("/landings/{landing_id}", response_model=LandingPageResponse)
async def get_landing_public(
    landing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> LandingPage:
    result = await db.execute(select(LandingPage).where(LandingPage.id == landing_id))
    landing = result.scalar_one_or_none()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    # Incrementar views
    landing.views = (landing.views or 0) + 1
    await db.commit()
    await db.refresh(landing)
    return landing


@router.patch("/landings/{landing_id}", response_model=LandingPageResponse)
async def update_landing(
    landing_id: uuid.UUID,
    body: LandingPageUpdate,
    current_user: User = Depends(permissions.require_action("create_campaign")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> LandingPage:
    result = await db.execute(
        select(LandingPage).where(LandingPage.id == landing_id, LandingPage.client_account_id == client_account.id)
    )
    landing = result.scalar_one_or_none()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(landing, field, value)
    await db.commit()
    await db.refresh(landing)
    return landing


@router.post("/landings/{landing_id}/submit", response_model=LeadResponse)
async def submit_lead(
    landing_id: uuid.UUID,
    body: LeadSubmit,
    db: AsyncSession = Depends(get_db),
) -> Lead:
    result = await db.execute(select(LandingPage).where(LandingPage.id == landing_id))
    landing = result.scalar_one_or_none()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    lead = Lead(
        landing_page_id=landing.id,
        plan_id=landing.plan_id,
        user_id=landing.user_id,
        client_account_id=landing.client_account_id,
        email=body.email,
        nombre=body.nombre,
        empresa=body.empresa,
        telefono=body.telefono,
        num_empleados=body.num_empleados,
        extra_data=body.extra_data,
    )
    db.add(lead)
    landing.conversions = (landing.conversions or 0) + 1
    await db.commit()
    await db.refresh(lead)
    return lead


# ─── Thanks page (pública) ────────────────────────────────────────────────────

@router.get("/landings/{landing_id}/thanks", response_model=ThanksPageData)
async def get_thanks_page(
    landing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ThanksPageData:
    landing_result = await db.execute(select(LandingPage).where(LandingPage.id == landing_id))
    landing = landing_result.scalar_one_or_none()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    thanks_data = ThanksPageData(
        primary_color=landing.primary_color,
        logo_url=landing.logo_url,
    )

    # Buscar thanks_page en output del EmailAgent
    task_result = await db.execute(
        select(AgentTask).where(
            AgentTask.plan_id == landing.plan_id,
            AgentTask.agent_name == "EmailAgent",
            AgentTask.status == "completed",
        )
    )
    email_task = task_result.scalar_one_or_none()
    if email_task and email_task.output:
        tp = email_task.output.get("thanks_page") or {}
        if tp:
            thanks_data.headline = tp.get("headline", thanks_data.headline)
            thanks_data.subheadline = tp.get("subheadline", thanks_data.subheadline)
            thanks_data.next_step_title = tp.get("next_step_title")
            thanks_data.next_step_description = tp.get("next_step_description")
            thanks_data.cta_text = tp.get("cta_text")
            thanks_data.cta_url = tp.get("cta_url")
            thanks_data.ps_text = tp.get("ps_text")

    # Buscar lead magnet del plan
    lm_result = await db.execute(
        select(LeadMagnet).where(LeadMagnet.plan_id == landing.plan_id)
    )
    lm = lm_result.scalar_one_or_none()
    if lm and lm.pdf_url:
        thanks_data.lead_magnet_url = lm.pdf_url
        thanks_data.lead_magnet_title = lm.title

    return thanks_data
