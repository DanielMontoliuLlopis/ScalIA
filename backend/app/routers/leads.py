import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_active_client_account, get_current_user
from app.database import get_db
from app.models.client_account import ClientAccount
from app.models.landing_page import LandingPage
from app.models.lead import Lead
from app.models.plan import Plan
from app.models.sequence_event import SequenceEvent
from app.models.task import AgentTask
from app.models.user import User
from app.models.user_settings import UserSettings
from app.services import permissions
from app.schemas.campaign import LeadDetail as LeadDetailSchema

router = APIRouter(prefix="/leads", tags=["leads"])

VALID_STATUSES = {"new", "contacted", "showed_up", "closed", "lost"}


class LeadSubmit(BaseModel):
    landing_page_id: uuid.UUID
    email: EmailStr
    nombre: str | None = None
    empresa: str | None = None
    telefono: str | None = None
    num_empleados: str | None = None
    extra_data: dict = {}


class LeadResponse(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


@router.post("", response_model=LeadResponse)
async def submit_lead(
    body: LeadSubmit,
    db: AsyncSession = Depends(get_db),
) -> LeadResponse:
    result = await db.execute(
        select(LandingPage).where(LandingPage.id == body.landing_page_id)
    )
    landing = result.scalar_one_or_none()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing page not found")

    lead = Lead(
        landing_page_id=landing.id,
        plan_id=landing.plan_id,
        user_id=landing.user_id,
        client_account_id=landing.client_account_id,
        email=str(body.email),
        nombre=body.nombre,
        empresa=body.empresa,
        telefono=body.telefono,
        num_empleados=body.num_empleados,
        extra_data=body.extra_data,
    )

    # Scoring CRM determinista
    from app.agents.crm import score_lead
    lead_data_for_scoring = {
        "email": str(body.email),
        "nombre": body.nombre,
        "empresa": body.empresa,
        "telefono": body.telefono,
        "num_empleados": body.num_empleados,
        "extra_data": body.extra_data,
    }
    scoring = score_lead(landing.form_fields or [], lead_data_for_scoring)
    lead.score = scoring["score"]
    lead.segment = scoring["segment"]
    lead.scoring_breakdown = scoring["breakdown"]
    lead.recommended_action = scoring.get("recommended_action")

    db.add(lead)

    landing.conversions = landing.conversions + 1

    await db.flush()

    await _trigger_sequences(db, lead, landing)

    await db.commit()
    await db.refresh(lead)

    return LeadResponse(id=lead.id, email=lead.email, created_at=lead.created_at)


class LeadPipelineUpdate(BaseModel):
    lead_status: str | None = None
    closed_value: float | None = None


@router.patch("/{lead_id}", response_model=LeadDetailSchema)
async def update_lead_pipeline(
    lead_id: uuid.UUID,
    body: LeadPipelineUpdate,
    current_user: User = Depends(permissions.require_action("edit_leads")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> LeadDetailSchema:
    lead = (await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.client_account_id == client_account.id)
    )).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    now = datetime.now(timezone.utc)

    if body.lead_status is not None:
        if body.lead_status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"lead_status inválido: {body.lead_status}")
        prev_status = lead.lead_status
        lead.lead_status = body.lead_status
        if body.lead_status == "showed_up" and not lead.showed_up_at:
            lead.showed_up_at = now
        if body.lead_status == "closed" and not lead.closed_at:
            lead.closed_at = now
        if body.lead_status == "contacted" and prev_status == "new" and not lead.meeting_scheduled_at:
            lead.meeting_scheduled_at = now

    if body.closed_value is not None:
        lead.closed_value = Decimal(str(body.closed_value))

    # Re-scoring on status change
    if body.lead_status is not None:
        from app.agents.crm import rescore_on_status_change
        from app.models.landing_page import LandingPage as LP
        lp = (await db.execute(select(LP).where(LP.id == lead.landing_page_id))).scalar_one_or_none()
        form_fields = lp.form_fields if lp else []
        lead_data = {
            "email": lead.email,
            "nombre": lead.nombre,
            "empresa": lead.empresa,
            "telefono": lead.telefono,
            "num_empleados": lead.num_empleados,
            "extra_data": lead.extra_data or {},
        }
        rescore = rescore_on_status_change(lead_data, form_fields, body.lead_status)
        lead.score = rescore["score"]
        lead.segment = rescore["segment"]
        lead.scoring_breakdown = rescore["breakdown"]
        lead.recommended_action = rescore["recommended_action"]

    await db.commit()
    await db.refresh(lead)

    events = (await db.execute(
        select(SequenceEvent).where(SequenceEvent.lead_id == lead.id).order_by(SequenceEvent.order.asc())
    )).scalars().all()
    email_events = [e for e in events if e.channel == "email"]
    wa_events = [e for e in events if e.channel == "whatsapp"]

    from app.routers.campaigns import _compute_sequence_status
    seq_status = _compute_sequence_status(email_events, wa_events)

    return LeadDetailSchema(
        id=lead.id,
        email=lead.email,
        nombre=lead.nombre,
        empresa=lead.empresa,
        telefono=lead.telefono,
        num_empleados=lead.num_empleados,
        score=lead.score,
        segment=lead.segment,
        recommended_action=lead.recommended_action,
        action_completed_at=lead.action_completed_at,
        action_note=lead.action_note,
        scoring_breakdown=lead.scoring_breakdown,
        extra_data=lead.extra_data or {},
        sequence_status=seq_status,
        sequence_events=[
            {
                "id": str(e.id),
                "channel": e.channel,
                "order": e.order,
                "subject": e.subject,
                "preview": e.preview,
                "status": e.status,
                "scheduled_at": e.scheduled_at.isoformat() if e.scheduled_at else None,
                "sent_at": e.sent_at.isoformat() if e.sent_at else None,
            }
            for e in events
        ],
        lead_status=lead.lead_status,
        closed_value=lead.closed_value,
        meeting_scheduled_at=lead.meeting_scheduled_at,
        showed_up_at=lead.showed_up_at,
        closed_at=lead.closed_at,
        created_at=lead.created_at,
    )


async def _trigger_sequences(
    db: AsyncSession,
    lead: Lead,
    landing: LandingPage,
) -> None:
    """Sends email #1 and WhatsApp #1 immediately; schedules the rest via Celery.
    Also records every step as a SequenceEvent for per-lead tracking."""
    try:
        settings_result = await db.execute(
            select(UserSettings).where(UserSettings.client_account_id == landing.client_account_id)
        )
        user_settings = settings_result.scalar_one_or_none()
        if not user_settings:
            return

        task_result = await db.execute(
            select(AgentTask).where(
                AgentTask.plan_id == landing.plan_id,
                AgentTask.agent_name == "EmailAgent",
            )
        )
        email_task = task_result.scalar_one_or_none()
        if not email_task or not email_task.output:
            return

        agent_output = email_task.output
        ca_id_str = str(landing.client_account_id)

        await _dispatch_email_sequence(db, user_settings, agent_output, lead, ca_id_str)

        if lead.telefono:
            await _dispatch_whatsapp_sequence(db, user_settings, agent_output, lead, ca_id_str)

    except Exception as exc:
        print(f"[Leads] Sequence dispatch failed: {exc}")


def _record_event(
    db: AsyncSession,
    lead: Lead,
    channel: str,
    order: int,
    subject: str | None,
    preview: str | None,
    delay_hours: int,
    status: str,
) -> SequenceEvent:
    now = datetime.now(timezone.utc)
    scheduled_at = now + timedelta(hours=delay_hours)
    event = SequenceEvent(
        lead_id=lead.id,
        plan_id=lead.plan_id,
        user_id=lead.user_id,
        client_account_id=lead.client_account_id,
        channel=channel,
        order=order,
        subject=subject,
        preview=preview,
        status=status,
        scheduled_at=scheduled_at,
        sent_at=now if status == "sent" else None,
    )
    db.add(event)
    return event


async def _dispatch_email_sequence(
    db: AsyncSession,
    user_settings: UserSettings,
    agent_output: dict,
    lead: Lead,
    ca_id_str: str,
) -> None:
    from app.tools.resend import send_email
    from app.workers.email_tasks import send_sequence_email

    emails = agent_output.get("email_sequence", {}).get("emails", [])
    has_key = bool(user_settings.resend_api_key)
    from_email = user_settings.resend_from_email or "noreply@growthOS.app"

    for i, email in enumerate(emails):
        delay_hours = email.get("send_delay_hours", 0)
        subject = email.get("subject", "")
        preview = email.get("preview_text") or ""
        body_html = email.get("body_html", "")
        order = email.get("order", i + 1)

        if not has_key:
            _record_event(db, lead, "email", order, subject, preview, delay_hours, "skipped")
            continue

        if delay_hours == 0:
            try:
                await send_email(
                    api_key=user_settings.resend_api_key,
                    from_email=from_email,
                    to=lead.email,
                    subject=subject,
                    html=body_html,
                )
                _record_event(db, lead, "email", order, subject, preview, 0, "sent")
            except Exception as exc:
                ev = _record_event(db, lead, "email", order, subject, preview, 0, "failed")
                ev.error = str(exc)[:500]
        else:
            event = _record_event(db, lead, "email", order, subject, preview, delay_hours, "scheduled")
            await db.flush()
            send_sequence_email.apply_async(
                args=[ca_id_str, lead.email, subject, body_html, str(event.id), str(lead.id)],
                countdown=delay_hours * 3600,
            )


async def _dispatch_whatsapp_sequence(
    db: AsyncSession,
    user_settings: UserSettings,
    agent_output: dict,
    lead: Lead,
    ca_id_str: str,
) -> None:
    from app.tools.whatsapp import send_whatsapp_text
    from app.workers.email_tasks import send_sequence_whatsapp

    messages = agent_output.get("whatsapp_sequence", {}).get("messages", [])
    has_wa = bool(user_settings.whatsapp_phone_number_id and user_settings.meta_access_token)

    for i, msg in enumerate(messages):
        delay_hours = msg.get("send_delay_hours", 0)
        text = msg.get("text", "")
        order = msg.get("order", i + 1)
        preview = text[:200] if text else None

        if not text:
            continue

        if not has_wa:
            _record_event(db, lead, "whatsapp", order, None, preview, delay_hours, "skipped")
            continue

        if delay_hours == 0:
            try:
                await send_whatsapp_text(
                    access_token=user_settings.meta_access_token,
                    phone_number_id=user_settings.whatsapp_phone_number_id,
                    to_phone=lead.telefono,
                    message=text,
                )
                _record_event(db, lead, "whatsapp", order, None, preview, 0, "sent")
            except Exception as exc:
                ev = _record_event(db, lead, "whatsapp", order, None, preview, 0, "failed")
                ev.error = str(exc)[:500]
        else:
            event = _record_event(db, lead, "whatsapp", order, None, preview, delay_hours, "scheduled")
            await db.flush()
            send_sequence_whatsapp.apply_async(
                args=[ca_id_str, lead.telefono, text, str(event.id), str(lead.id)],
                countdown=delay_hours * 3600,
            )
