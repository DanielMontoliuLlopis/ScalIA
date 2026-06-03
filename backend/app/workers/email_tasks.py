import asyncio
from datetime import datetime, timezone

from app.workers.celery_app import celery_app


@celery_app.task(name="send_sequence_email", bind=True, max_retries=3, default_retry_delay=300)
def send_sequence_email(self, client_account_id: str, to_email: str, subject: str, body_html: str, event_id: str | None = None, lead_id: str | None = None) -> dict:
    """Sends a single email from a nurturing sequence. Skips if lead is closed/lost."""
    try:
        return asyncio.run(_send_email(client_account_id, to_email, subject, body_html, event_id, lead_id))
    except Exception as exc:
        if event_id:
            _mark_event(event_id, "failed", str(exc)[:500])
        raise self.retry(exc=exc)


@celery_app.task(name="send_sequence_whatsapp", bind=True, max_retries=3, default_retry_delay=300)
def send_sequence_whatsapp(self, client_account_id: str, to_phone: str, text: str, event_id: str | None = None, lead_id: str | None = None) -> dict:
    """Sends a single WhatsApp message from a nurturing sequence. Skips if lead is closed/lost."""
    try:
        return asyncio.run(_send_whatsapp(client_account_id, to_phone, text, event_id, lead_id))
    except Exception as exc:
        if event_id:
            _mark_event(event_id, "failed", str(exc)[:500])
        raise self.retry(exc=exc)


def _sync_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.config import settings
    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    engine = create_engine(sync_url, pool_pre_ping=True)
    return sessionmaker(engine), engine


def _get_lead_status(lead_id: str) -> str | None:
    """Returns lead_status or None if lead not found."""
    import uuid as _uuid
    from sqlalchemy import select
    from app.models.lead import Lead

    Session, engine = _sync_session()
    try:
        with Session() as db:
            lead = db.execute(
                select(Lead).where(Lead.id == _uuid.UUID(lead_id))
            ).scalar_one_or_none()
            return lead.lead_status if lead else None
    finally:
        engine.dispose()


def _should_skip_sequence(lead_id: str | None) -> bool:
    """Returns True if lead is closed or lost — sequence must stop."""
    if not lead_id:
        return False
    status = _get_lead_status(lead_id)
    return status in ("closed", "lost")


def _showed_up(lead_id: str | None) -> bool:
    if not lead_id:
        return False
    return _get_lead_status(lead_id) == "showed_up"


def _adapt_subject_for_showed_up(subject: str) -> str:
    """Prepend a context marker so showed-up leads get a warmer subject line."""
    return f"[Tras nuestra llamada] {subject}"


def _mark_event(event_id: str, status: str, error: str | None = None) -> None:
    import uuid as _uuid
    from sqlalchemy import select
    from app.models.sequence_event import SequenceEvent

    Session, engine = _sync_session()
    try:
        with Session() as db:
            ev = db.execute(
                select(SequenceEvent).where(SequenceEvent.id == _uuid.UUID(event_id))
            ).scalar_one_or_none()
            if ev:
                ev.status = status
                if status == "sent":
                    ev.sent_at = datetime.now(timezone.utc)
                if error:
                    ev.error = error
                db.commit()
    finally:
        engine.dispose()


async def _send_email(client_account_id: str, to_email: str, subject: str, body_html: str, event_id: str | None, lead_id: str | None) -> dict:
    import uuid
    from sqlalchemy import select
    from app.models.user_settings import UserSettings
    from app.tools.resend import send_email

    if _should_skip_sequence(lead_id):
        if event_id:
            _mark_event(event_id, "skipped", "lead closed or lost")
        return {"status": "skipped", "reason": "lead closed or lost"}

    showed_up = _showed_up(lead_id)
    if showed_up:
        subject = _adapt_subject_for_showed_up(subject)

    Session, engine = _sync_session()

    with Session() as db:
        row = db.execute(
            select(UserSettings).where(UserSettings.client_account_id == uuid.UUID(client_account_id))
        ).scalar_one_or_none()

    engine.dispose()

    if not row or not row.resend_api_key:
        if event_id:
            _mark_event(event_id, "skipped", "no resend key")
        return {"status": "skipped", "reason": "no resend key"}

    from_email = row.resend_from_email or "noreply@growthOS.app"

    result = await send_email(
        api_key=row.resend_api_key,
        from_email=from_email,
        to=to_email,
        subject=subject,
        html=body_html,
    )
    if event_id:
        _mark_event(event_id, "sent")
    return {"status": "sent", "id": result.get("id")}


async def _send_whatsapp(client_account_id: str, to_phone: str, text: str, event_id: str | None, lead_id: str | None) -> dict:
    import uuid
    from sqlalchemy import select
    from app.models.user_settings import UserSettings
    from app.tools.whatsapp import send_whatsapp_text

    if _should_skip_sequence(lead_id):
        if event_id:
            _mark_event(event_id, "skipped", "lead closed or lost")
        return {"status": "skipped", "reason": "lead closed or lost"}

    Session, engine = _sync_session()

    with Session() as db:
        row = db.execute(
            select(UserSettings).where(UserSettings.client_account_id == uuid.UUID(client_account_id))
        ).scalar_one_or_none()

    engine.dispose()

    if not row or not row.whatsapp_phone_number_id or not row.meta_access_token:
        if event_id:
            _mark_event(event_id, "skipped", "no whatsapp config")
        return {"status": "skipped", "reason": "no whatsapp config"}

    result = await send_whatsapp_text(
        access_token=row.meta_access_token,
        phone_number_id=row.whatsapp_phone_number_id,
        to_phone=to_phone,
        message=text,
    )
    if event_id:
        _mark_event(event_id, "sent")
    return {"status": "sent", "wa_id": result.get("messages", [{}])[0].get("id")}
