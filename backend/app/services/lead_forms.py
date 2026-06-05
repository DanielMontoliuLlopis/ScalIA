"""Resolución del formulario de Lead Ad al publicar una campaña instant_form.

- Si el plan tiene un LeadForm seleccionado → se asegura de que esté sincronizado en Meta.
- Si no hay ninguno → auto-crea uno por defecto (a partir del plan + Settings), lo guarda
  como plantilla reutilizable y lo sincroniza.

Devuelve el `meta_form_id` listo para inyectar en el campaign_json.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lead_form import LeadForm
from app.models.plan import Plan
from app.models.user_settings import UserSettings
from app.tools.meta_ads import MetaAdsError, create_leadgen_form

# Campos por defecto al auto-crear un formulario
_DEFAULT_FIELDS = [
    {"type": "prefill", "key": "FULL_NAME", "label": "Nombre completo"},
    {"type": "prefill", "key": "EMAIL", "label": "Email"},
    {"type": "prefill", "key": "PHONE", "label": "Teléfono"},
]
_B2B_FIELD = {"type": "prefill", "key": "COMPANY_NAME", "label": "Empresa"}


def _form_def(form: LeadForm) -> dict:
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


async def _sync_form(
    db: AsyncSession, form: LeadForm, access_token: str, page_id: str
) -> str:
    """Crea el formulario en Meta si aún no existe (o si la Page cambió) y persiste el id."""
    if form.meta_form_id and form.meta_page_id == page_id:
        return form.meta_form_id
    form_id = await create_leadgen_form(access_token, page_id, _form_def(form))
    form.meta_form_id = form_id
    form.meta_page_id = page_id
    form.synced_at = datetime.now(timezone.utc)
    await db.commit()
    return form_id


async def resolve_form_id_for_plan(
    db: AsyncSession, plan: Plan, settings: UserSettings
) -> str | None:
    """Devuelve el meta_form_id a usar para un plan instant_form. None si no aplica."""
    if (plan.funnel_type or "") != "instant_form":
        return None

    access_token = settings.meta_access_token or ""
    page_id = settings.meta_page_id or ""
    if not access_token or not page_id:
        raise MetaAdsError("Falta meta_access_token o meta_page_id en Settings")

    # 1) Form seleccionado por el usuario
    if plan.lead_form_id:
        form = (
            await db.execute(select(LeadForm).where(LeadForm.id == plan.lead_form_id))
        ).scalar_one_or_none()
        if form:
            return await _sync_form(db, form, access_token, page_id)

    # 2) Auto-crear un formulario por defecto desde el plan + Settings
    privacy_url = settings.privacy_policy_url
    if not privacy_url:
        raise MetaAdsError(
            "Para publicar un anuncio con formulario instantáneo necesitas una URL de "
            "política de privacidad. Añádela en Ajustes o crea un formulario en la "
            "sección Formularios."
        )

    business_type = settings.business_type or ""
    fields = list(_DEFAULT_FIELDS)
    if business_type in {"saas", "services"}:
        fields.append(_B2B_FIELD)

    company = settings.company_name or "tu negocio"
    form = LeadForm(
        client_account_id=plan.client_account_id,
        user_id=plan.user_id,
        name=(plan.title or f"Formulario {company}")[:200],
        locale="es_ES",
        intro_headline=plan.title[:300] if plan.title else None,
        fields=fields,
        privacy_policy_url=privacy_url,
        privacy_policy_link_text="Política de privacidad",
        thank_you_title="¡Gracias!",
        thank_you_body="Hemos recibido tus datos. Nos pondremos en contacto muy pronto.",
        thank_you_button_type="VIEW_WEBSITE",
        thank_you_website_url=plan.redirect_url,
        thank_you_button_text="Visitar web" if plan.redirect_url else None,
    )
    db.add(form)
    await db.flush()  # obtener id
    plan.lead_form_id = form.id
    form_id = await _sync_form(db, form, access_token, page_id)
    await db.commit()
    return form_id
