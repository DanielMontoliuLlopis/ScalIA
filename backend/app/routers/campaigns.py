import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, asc, case
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
from app.schemas.campaign import CampaignSummary, FunnelMetrics, LeadDetail, MetaInsights, PublishResult
from app.tools.meta_ads import (
    META_GRAPH_BASE,
    get_campaign_insights,
    publish_campaign,
    MetaAdsError,
)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

# Statuses that represent an active or completed campaign
CAMPAIGN_STATUSES = {
    "executing",
    "pending_ads_approval",
    "done",
    "pending_copy_approval",
}


# ─── List ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[CampaignSummary])
async def list_campaigns(
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[CampaignSummary]:
    plans_result = await db.execute(
        select(Plan)
        .where(
            Plan.client_account_id == client_account.id,
            Plan.status.in_(CAMPAIGN_STATUSES),
        )
        .order_by(Plan.created_at.desc())
    )
    plans = plans_result.scalars().all()
    if not plans:
        return []

    plan_ids = [p.id for p in plans]

    # Lista ligera: solo landings + conteo de leads (2 queries batch).
    # Los outputs pesados (ads/copy/email JSONB) NO viajan en la lista — el modal
    # los pide bajo demanda vía GET /campaigns/{id}.
    landings_result = await db.execute(
        select(LandingPage).where(LandingPage.plan_id.in_(plan_ids))
    )
    all_landings = landings_result.scalars().all()

    leads_count_result = await db.execute(
        select(Lead.plan_id, func.count().label("cnt"))
        .where(Lead.plan_id.in_(plan_ids))
        .group_by(Lead.plan_id)
    )
    leads_by_plan: dict = {row.plan_id: row.cnt for row in leads_count_result}

    landings_by_plan: dict[uuid.UUID, list[LandingPage]] = {}
    for l in all_landings:
        landings_by_plan.setdefault(l.plan_id, []).append(l)

    summaries: list[CampaignSummary] = []
    for plan in plans:
        landings = landings_by_plan.get(plan.id, [])
        summaries.append(_summary_from(plan, landings, leads_by_plan.get(plan.id, 0)))

    return summaries


def _summary_from(
    plan: Plan,
    landings: list[LandingPage],
    total_leads: int,
    *,
    ads_output: Any = None,
    copy_output: Any = None,
    email_output: Any = None,
) -> CampaignSummary:
    return CampaignSummary(
        plan_id=plan.id,
        title=plan.title,
        status=plan.status,
        created_at=plan.created_at,
        meta_campaign_id=plan.meta_campaign_id,
        total_views=sum(l.views for l in landings),
        total_conversions=sum(l.conversions for l in landings),
        total_leads=total_leads,
        landings=[
            {
                "id": l.id,
                "variant": l.variant,
                "headline": l.headline,
                "subheadline": l.subheadline,
                "benefits": l.benefits or [],
                "cta_text": l.cta_text,
                "hero_image_url": l.hero_image_url,
                "primary_color": l.primary_color,
                "views": l.views,
                "conversions": l.conversions,
            }
            for l in landings
        ],
        ads_output=ads_output,
        copy_output=copy_output,
        email_output=email_output,
        parent_plan_id=plan.parent_plan_id,
        is_offer_test=plan.is_offer_test,
        offer_test_label=plan.offer_test_label,
        ab_mode=plan.ab_mode or "ab_classic",
    )


# ─── Bulk metrics (desde snapshots, sin pegar a Meta) ─────────────────────────

class CampaignMetricsBulk(BaseModel):
    spend: float = 0.0
    impressions: int = 0
    clicks: int = 0
    reach: int = 0
    leads: int = 0
    revenue: float = 0.0
    ctr: float | None = None       # porcentaje, igual escala que Meta
    cpc: float | None = None
    roas: float | None = None


@router.get("/metrics/bulk", response_model=dict[str, CampaignMetricsBulk])
async def get_bulk_metrics(
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> dict[str, CampaignMetricsBulk]:
    """Métricas agregadas de TODAS las campañas en 1 query, leyendo de
    `metric_snapshots` (las puebla el beat horario). Reemplaza las 2N llamadas
    en vivo a Meta (/metrics + /meta-insights) que hacía la lista de campañas."""
    from app.models.metric_snapshot import MetricSnapshot

    rows = await db.execute(
        select(
            MetricSnapshot.plan_id,
            func.sum(MetricSnapshot.spend),
            func.sum(MetricSnapshot.impressions),
            func.sum(MetricSnapshot.clicks),
            func.sum(MetricSnapshot.reach),
            func.sum(MetricSnapshot.leads),
            func.sum(MetricSnapshot.revenue),
        )
        .where(
            MetricSnapshot.client_account_id == client_account.id,
            MetricSnapshot.level == "campaign",
            MetricSnapshot.breakdown_key == "",
        )
        .group_by(MetricSnapshot.plan_id)
    )

    out: dict[str, CampaignMetricsBulk] = {}
    for plan_id, spend, impr, clicks, reach, leads, revenue in rows:
        spend = float(spend or 0)
        impr = int(impr or 0)
        clicks = int(clicks or 0)
        revenue = float(revenue or 0)
        out[str(plan_id)] = CampaignMetricsBulk(
            spend=spend,
            impressions=impr,
            clicks=clicks,
            reach=int(reach or 0),
            leads=int(leads or 0),
            revenue=revenue,
            ctr=(clicks / impr * 100) if impr else None,
            cpc=(spend / clicks) if clicks else None,
            roas=(revenue / spend) if spend else None,
        )
    return out


# ─── Detalle de una campaña (outputs pesados bajo demanda) ────────────────────

@router.get("/{plan_id}", response_model=CampaignSummary)
async def get_campaign_detail(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> CampaignSummary:
    """Detalle completo de una campaña, incluyendo los outputs de AdsAgent/
    CopyAgent/EmailAgent. Lo pide el modal al abrirse — no en la lista."""
    plan = (await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    landings = (await db.execute(
        select(LandingPage).where(LandingPage.plan_id == plan_id)
    )).scalars().all()

    total_leads = (await db.execute(
        select(func.count()).where(Lead.plan_id == plan_id)
    )).scalar() or 0

    tasks = (await db.execute(
        select(AgentTask).where(
            AgentTask.plan_id == plan_id,
            AgentTask.agent_name.in_(["AdsAgent", "CopyAgent", "EmailAgent"]),
            AgentTask.status == "completed",
        )
    )).scalars().all()
    ads_output = next((t.output for t in tasks if t.agent_name == "AdsAgent"), None)
    copy_output = next((t.output for t in tasks if t.agent_name == "CopyAgent"), None)
    email_output = next((t.output for t in tasks if t.agent_name == "EmailAgent"), None)

    return _summary_from(
        plan, landings, total_leads,
        ads_output=ads_output, copy_output=copy_output, email_output=email_output,
    )


# ─── Meta status (lock check) ─────────────────────────────────────────────────

class MetaStatusResponse(BaseModel):
    has_meta_campaign: bool
    meta_status: str | None = None        # ACTIVE | PAUSED | DELETED | ARCHIVED | None
    is_locked: bool = False               # ACTIVE → cannot edit
    error: str | None = None


@router.get("/{plan_id}/meta-status", response_model=MetaStatusResponse)
async def get_meta_status(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> MetaStatusResponse:
    plan = (await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    if not plan.meta_campaign_id:
        return MetaStatusResponse(has_meta_campaign=False)

    settings = (await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account.id)
    )).scalar_one_or_none()

    if not settings or not settings.meta_access_token:
        return MetaStatusResponse(
            has_meta_campaign=True,
            error="Meta access token no configurado",
        )

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{META_GRAPH_BASE}/{plan.meta_campaign_id}",
                params={
                    "fields": "status,effective_status",
                    "access_token": settings.meta_access_token,
                },
            )
        body = resp.json()
        if "error" in body:
            return MetaStatusResponse(
                has_meta_campaign=True,
                error=body["error"].get("message", "error meta"),
            )
        effective = body.get("effective_status") or body.get("status")
        return MetaStatusResponse(
            has_meta_campaign=True,
            meta_status=effective,
            is_locked=(effective == "ACTIVE"),
        )
    except Exception as exc:
        return MetaStatusResponse(has_meta_campaign=True, error=str(exc)[:200])


# ─── PATCH campaign — editar antes de publicar ────────────────────────────────

class CampaignUpdate(BaseModel):
    """Edición de campos pre-publicación. Solo permitido si NO está ACTIVE en Meta.

    Cubre todo lo configurable en Meta: campaña, ad set, targeting, pixel/eventos,
    reglas (atribución, frequency cap), creativos y landings.
    """
    # ── Campaña ──────────────────────────────────────────────────────────────
    campaign_name: str | None = None
    objective: str | None = None
    buying_type: str | None = None
    campaign_budget_optimization: bool | None = None
    daily_budget_eur: float | None = None
    lifetime_budget_eur: float | None = None
    spend_cap_eur: float | None = None
    campaign_bid_strategy: str | None = None
    bid_cap_eur: float | None = None
    campaign_start_time: str | None = None
    campaign_stop_time: str | None = None
    special_ad_categories: list[str] | None = None
    special_ad_category_country: list[str] | None = None
    # ── Ad set: entrega / optimización ────────────────────────────────────────
    adset_name: str | None = None
    optimization_goal: str | None = None
    billing_event: str | None = None
    bid_strategy: str | None = None
    bid_amount_eur: float | None = None
    adset_daily_budget_eur: float | None = None
    adset_lifetime_budget_eur: float | None = None
    adset_start_time: str | None = None
    adset_end_time: str | None = None
    destination_type: str | None = None
    pacing_type: list[str] | None = None
    is_dynamic_creative: bool | None = None
    advantage_audience: bool | None = None
    dsa_beneficiary: str | None = None
    dsa_payor: str | None = None
    # ── Pixel / eventos (promoted_object) ─────────────────────────────────────
    pixel_id: str | None = None
    custom_event_type: str | None = None
    page_id: str | None = None
    application_id: str | None = None
    offsite_conversion_event_id: str | None = None
    # ── Reglas: atribución + frequency cap ────────────────────────────────────
    attribution_spec: list[dict[str, Any]] | None = None
    frequency_control_specs: list[dict[str, Any]] | None = None
    # ── Targeting ─────────────────────────────────────────────────────────────
    age_min: int | None = None
    age_max: int | None = None
    genders: list[int] | None = None
    countries: list[str] | None = None
    excluded_countries: list[str] | None = None
    publisher_platforms: list[str] | None = None
    facebook_positions: list[str] | None = None
    instagram_positions: list[str] | None = None
    audience_network_positions: list[str] | None = None
    messenger_positions: list[str] | None = None
    device_platforms: list[str] | None = None
    # Segmentación detallada — listas de { id, name }
    interests: list[dict[str, Any]] | None = None
    behaviors: list[dict[str, Any]] | None = None
    demographics: list[dict[str, Any]] | None = None
    work_positions: list[dict[str, Any]] | None = None
    custom_audiences: list[dict[str, Any]] | None = None
    excluded_custom_audiences: list[dict[str, Any]] | None = None
    # ── Ads (A/B) — { variant, headline, description, message, caption, link, cta, conversion_domain, url_tags } ──
    ads: list[dict[str, Any]] | None = None
    # ── Landings — { id, headline, subheadline, benefits, cta_text, primary_color } ──
    landings: list[dict[str, Any]] | None = None
    # ── Ad sets adicionales (Fase 3) — reemplazo completo del array ──
    additional_ad_sets: list[dict[str, Any]] | None = None


@router.patch("/{plan_id}", response_model=CampaignSummary)
async def update_campaign(
    plan_id: uuid.UUID,
    body: CampaignUpdate,
    current_user: User = Depends(permissions.require_action("create_campaign")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> CampaignSummary:
    plan = (await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Bloquear si ACTIVE en Meta
    if plan.meta_campaign_id:
        settings = (await db.execute(
            select(UserSettings).where(UserSettings.client_account_id == client_account.id)
        )).scalar_one_or_none()
        if settings and settings.meta_access_token:
            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    resp = await client.get(
                        f"{META_GRAPH_BASE}/{plan.meta_campaign_id}",
                        params={
                            "fields": "effective_status",
                            "access_token": settings.meta_access_token,
                        },
                    )
                body_resp = resp.json()
                eff = body_resp.get("effective_status")
                if eff == "ACTIVE":
                    raise HTTPException(
                        status_code=403,
                        detail="La campaña está ACTIVA en Meta. Pausa la campaña antes de editar.",
                    )
            except HTTPException:
                raise
            except Exception:
                pass  # si falla la consulta, permitimos edición

    # Localizar AdsAgent task
    ads_task = (await db.execute(
        select(AgentTask).where(
            AgentTask.plan_id == plan_id,
            AgentTask.agent_name == "AdsAgent",
            AgentTask.status == "completed",
        )
    )).scalar_one_or_none()
    if not ads_task or not ads_task.output:
        raise HTTPException(status_code=400, detail="AdsAgent aún no ha generado la campaña.")

    output = dict(ads_task.output)
    cj = dict(output.get("campaign_json", {}))
    campaign = dict(cj.get("campaign", {}))
    ad_set = dict(cj.get("ad_set", {}))
    targeting = dict(ad_set.get("targeting", {}))
    geo = dict(targeting.get("geo_locations", {}))
    excluded_geo = dict(targeting.get("excluded_geo_locations", {}))
    promoted = dict(ad_set.get("promoted_object", {}))
    automation = dict(ad_set.get("targeting_automation", {}))

    def _eur_to_cents(v: float) -> int:
        return int(round(v * 100))

    def _set_or_clear(d: dict, key: str, value: Any) -> None:
        """Texto vacío → borra la clave; valor → la asigna."""
        if value is None:
            return
        if isinstance(value, str) and value.strip() == "":
            d.pop(key, None)
        else:
            d[key] = value

    # ── Campaña ─────────────────────────────────────────────────────────────
    if body.campaign_name is not None:
        campaign["name"] = body.campaign_name
        plan.title = body.campaign_name
    if body.objective is not None:
        campaign["objective"] = body.objective
    if body.buying_type is not None:
        campaign["buying_type"] = body.buying_type
    if body.campaign_budget_optimization is not None:
        campaign["campaign_budget_optimization"] = body.campaign_budget_optimization
    if body.daily_budget_eur is not None:
        daily_cents = _eur_to_cents(body.daily_budget_eur)
        campaign["daily_budget"] = daily_cents
        budget = dict(output.get("budget", {}))
        budget["daily_eur"] = body.daily_budget_eur
        budget["monthly_eur"] = round(body.daily_budget_eur * 30, 2)
        budget["daily_cents"] = daily_cents
        output["budget"] = budget
        output["budget_summary"] = (
            f"€{budget['monthly_eur']}/mes ÷ 30 = €{body.daily_budget_eur}/día"
        )
    if body.lifetime_budget_eur is not None:
        if body.lifetime_budget_eur > 0:
            campaign["lifetime_budget"] = _eur_to_cents(body.lifetime_budget_eur)
        else:
            campaign.pop("lifetime_budget", None)
    if body.spend_cap_eur is not None:
        if body.spend_cap_eur > 0:
            campaign["spend_cap"] = _eur_to_cents(body.spend_cap_eur)
        else:
            campaign.pop("spend_cap", None)
    if body.campaign_bid_strategy is not None:
        campaign["bid_strategy"] = body.campaign_bid_strategy
    if body.bid_cap_eur is not None:
        if body.bid_cap_eur > 0:
            campaign["bid_cap"] = _eur_to_cents(body.bid_cap_eur)
        else:
            campaign.pop("bid_cap", None)
    _set_or_clear(campaign, "start_time", body.campaign_start_time)
    _set_or_clear(campaign, "stop_time", body.campaign_stop_time)
    if body.special_ad_categories is not None:
        campaign["special_ad_categories"] = body.special_ad_categories
    if body.special_ad_category_country is not None:
        if body.special_ad_category_country:
            campaign["special_ad_category_country"] = body.special_ad_category_country
        else:
            campaign.pop("special_ad_category_country", None)

    # ── Ad set: entrega / optimización ────────────────────────────────────────
    if body.adset_name is not None:
        ad_set["name"] = body.adset_name
    if body.optimization_goal is not None:
        ad_set["optimization_goal"] = body.optimization_goal
    if body.billing_event is not None:
        ad_set["billing_event"] = body.billing_event
    if body.bid_strategy is not None:
        ad_set["bid_strategy"] = body.bid_strategy
    if body.bid_amount_eur is not None:
        if body.bid_amount_eur > 0:
            ad_set["bid_amount"] = _eur_to_cents(body.bid_amount_eur)
        else:
            ad_set.pop("bid_amount", None)
    if body.adset_daily_budget_eur is not None:
        if body.adset_daily_budget_eur > 0:
            ad_set["daily_budget"] = _eur_to_cents(body.adset_daily_budget_eur)
        else:
            ad_set.pop("daily_budget", None)
    if body.adset_lifetime_budget_eur is not None:
        if body.adset_lifetime_budget_eur > 0:
            ad_set["lifetime_budget"] = _eur_to_cents(body.adset_lifetime_budget_eur)
        else:
            ad_set.pop("lifetime_budget", None)
    _set_or_clear(ad_set, "start_time", body.adset_start_time)
    _set_or_clear(ad_set, "end_time", body.adset_end_time)
    if body.destination_type is not None:
        _set_or_clear(ad_set, "destination_type", body.destination_type)
    if body.pacing_type is not None:
        if body.pacing_type:
            ad_set["pacing_type"] = body.pacing_type
        else:
            ad_set.pop("pacing_type", None)
    if body.is_dynamic_creative is not None:
        ad_set["is_dynamic_creative"] = body.is_dynamic_creative
    if body.advantage_audience is not None:
        automation["advantage_audience"] = 1 if body.advantage_audience else 0
    _set_or_clear(ad_set, "dsa_beneficiary", body.dsa_beneficiary)
    _set_or_clear(ad_set, "dsa_payor", body.dsa_payor)

    # ── Pixel / eventos (promoted_object) ─────────────────────────────────────
    _set_or_clear(promoted, "pixel_id", body.pixel_id)
    _set_or_clear(promoted, "custom_event_type", body.custom_event_type)
    _set_or_clear(promoted, "page_id", body.page_id)
    _set_or_clear(promoted, "application_id", body.application_id)
    _set_or_clear(promoted, "offsite_conversion_event_id", body.offsite_conversion_event_id)

    # ── Reglas: atribución + frequency cap ────────────────────────────────────
    if body.attribution_spec is not None:
        if body.attribution_spec:
            ad_set["attribution_spec"] = body.attribution_spec
        else:
            ad_set.pop("attribution_spec", None)
    if body.frequency_control_specs is not None:
        if body.frequency_control_specs:
            ad_set["frequency_control_specs"] = body.frequency_control_specs
        else:
            ad_set.pop("frequency_control_specs", None)

    # ── Targeting ─────────────────────────────────────────────────────────────
    if body.age_min is not None:
        targeting["age_min"] = body.age_min
    if body.age_max is not None:
        targeting["age_max"] = body.age_max
    if body.genders is not None:
        if body.genders:
            targeting["genders"] = body.genders
        else:
            targeting.pop("genders", None)  # vacío = todos
    if body.countries is not None:
        geo["countries"] = body.countries
    if body.excluded_countries is not None:
        if body.excluded_countries:
            excluded_geo["countries"] = body.excluded_countries
        else:
            excluded_geo.pop("countries", None)
    if body.publisher_platforms is not None:
        targeting["publisher_platforms"] = body.publisher_platforms
    if body.facebook_positions is not None:
        targeting["facebook_positions"] = body.facebook_positions
    if body.instagram_positions is not None:
        targeting["instagram_positions"] = body.instagram_positions
    if body.audience_network_positions is not None:
        if body.audience_network_positions:
            targeting["audience_network_positions"] = body.audience_network_positions
        else:
            targeting.pop("audience_network_positions", None)
    if body.messenger_positions is not None:
        if body.messenger_positions:
            targeting["messenger_positions"] = body.messenger_positions
        else:
            targeting.pop("messenger_positions", None)
    if body.device_platforms is not None:
        targeting["device_platforms"] = body.device_platforms

    # ── Segmentación detallada (intereses / flexible_spec / audiencias) ───────
    if body.interests is not None:
        if body.interests:
            targeting["interests"] = body.interests
        else:
            targeting.pop("interests", None)

    flexible_spec = list(targeting.get("flexible_spec", []))
    flex0 = dict(flexible_spec[0]) if flexible_spec else {}
    flex_touched = False
    for field, value in (
        ("behaviors", body.behaviors),
        ("demographics", body.demographics),
        ("work_positions", body.work_positions),
    ):
        if value is not None:
            flex_touched = True
            if value:
                flex0[field] = value
            else:
                flex0.pop(field, None)
    if flex_touched:
        if flex0:
            if flexible_spec:
                flexible_spec[0] = flex0
            else:
                flexible_spec = [flex0]
            targeting["flexible_spec"] = flexible_spec
        else:
            # flex0 quedó vacío → eliminar el primer grupo
            flexible_spec = flexible_spec[1:]
            if flexible_spec:
                targeting["flexible_spec"] = flexible_spec
            else:
                targeting.pop("flexible_spec", None)

    if body.custom_audiences is not None:
        if body.custom_audiences:
            targeting["custom_audiences"] = body.custom_audiences
        else:
            targeting.pop("custom_audiences", None)

    if body.excluded_custom_audiences is not None:
        exclusions = dict(targeting.get("exclusions", {}))
        if body.excluded_custom_audiences:
            exclusions["custom_audiences"] = body.excluded_custom_audiences
            targeting["exclusions"] = exclusions
        else:
            exclusions.pop("custom_audiences", None)
            if exclusions:
                targeting["exclusions"] = exclusions
            else:
                targeting.pop("exclusions", None)

    # Reensamblar estructuras anidadas
    if geo:
        targeting["geo_locations"] = geo
    if excluded_geo:
        targeting["excluded_geo_locations"] = excluded_geo
    elif "excluded_geo_locations" in targeting:
        targeting.pop("excluded_geo_locations", None)
    if promoted:
        ad_set["promoted_object"] = promoted
    if automation:
        ad_set["targeting_automation"] = automation
    ad_set["targeting"] = targeting
    cj["ad_set"] = ad_set
    cj["campaign"] = campaign

    # ── Ads (A/B) ───────────────────────────────────────────────────────────
    if body.ads is not None:
        current_ads = list(cj.get("ads", []))
        for update_ad in body.ads:
            variant = update_ad.get("variant")
            target = next((a for a in current_ads if a.get("variant") == variant), None)
            if not target:
                continue
            if "conversion_domain" in update_ad:
                _set_or_clear(target, "conversion_domain", update_ad["conversion_domain"])
            creative = dict(target.get("creative") or {})
            if "url_tags" in update_ad:
                _set_or_clear(creative, "url_tags", update_ad["url_tags"])
            spec = dict(creative.get("object_story_spec") or {})
            link_data = dict(spec.get("link_data") or {})
            if "headline" in update_ad:
                link_data["name"] = update_ad["headline"]
            if "description" in update_ad:
                link_data["description"] = update_ad["description"]
            if "message" in update_ad:
                link_data["message"] = update_ad["message"]
            if "caption" in update_ad:
                _set_or_clear(link_data, "caption", update_ad["caption"])
            if "link" in update_ad:
                _set_or_clear(link_data, "link", update_ad["link"])
            if "cta" in update_ad:
                cta = dict(link_data.get("call_to_action") or {})
                cta["type"] = update_ad["cta"]
                link_data["call_to_action"] = cta
            spec["link_data"] = link_data
            creative["object_story_spec"] = spec
            target["creative"] = creative
        cj["ads"] = current_ads

    # ── Ad sets adicionales: reemplazo completo del array (incluye eliminar) ──
    if body.additional_ad_sets is not None:
        if body.additional_ad_sets:
            cj["additional_ad_sets"] = body.additional_ad_sets
        else:
            cj.pop("additional_ad_sets", None)

    output["campaign_json"] = cj
    ads_task.output = output

    # ── Landings ────────────────────────────────────────────────────────────
    if body.landings is not None:
        for lp in body.landings:
            lp_id = lp.get("id")
            if not lp_id:
                continue
            landing = (await db.execute(
                select(LandingPage).where(LandingPage.id == uuid.UUID(str(lp_id)))
            )).scalar_one_or_none()
            if not landing or landing.client_account_id != client_account.id:
                continue
            if "headline" in lp:
                landing.headline = lp["headline"]
            if "subheadline" in lp:
                landing.subheadline = lp["subheadline"]
            if "benefits" in lp:
                landing.benefits = lp["benefits"]
            if "cta_text" in lp:
                landing.cta_text = lp["cta_text"]
            if "primary_color" in lp:
                landing.primary_color = lp["primary_color"]

    await db.commit()

    # Devolver el summary actualizado
    return await _build_summary(db, plan)


async def _build_summary(db: AsyncSession, plan: Plan) -> CampaignSummary:
    landings = (await db.execute(
        select(LandingPage).where(LandingPage.plan_id == plan.id)
    )).scalars().all()
    total_leads = (await db.execute(
        select(func.count()).where(Lead.plan_id == plan.id)
    )).scalar() or 0
    tasks = (await db.execute(
        select(AgentTask).where(
            AgentTask.plan_id == plan.id,
            AgentTask.agent_name.in_(["AdsAgent", "CopyAgent", "EmailAgent"]),
            AgentTask.status == "completed",
        )
    )).scalars().all()
    ads_output = next((t.output for t in tasks if t.agent_name == "AdsAgent"), None)
    copy_output = next((t.output for t in tasks if t.agent_name == "CopyAgent"), None)
    email_output = next((t.output for t in tasks if t.agent_name == "EmailAgent"), None)

    return CampaignSummary(
        plan_id=plan.id,
        title=plan.title,
        status=plan.status,
        created_at=plan.created_at,
        meta_campaign_id=plan.meta_campaign_id,
        total_views=sum(l.views for l in landings),
        total_conversions=sum(l.conversions for l in landings),
        total_leads=total_leads,
        landings=[
            {
                "id": l.id, "variant": l.variant, "headline": l.headline,
                "subheadline": l.subheadline, "benefits": l.benefits or [],
                "cta_text": l.cta_text,
                "hero_image_url": l.hero_image_url, "primary_color": l.primary_color,
                "views": l.views, "conversions": l.conversions,
            }
            for l in landings
        ],
        ads_output=ads_output,
        copy_output=copy_output,
        email_output=email_output,
        ab_mode=plan.ab_mode or "ab_classic",
    )


# ─── Publish (sin cambios) ────────────────────────────────────────────────────

@router.post("/{plan_id}/publish", response_model=PublishResult)
async def publish_meta_campaign(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> PublishResult:
    plan_result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    # Ya publicado → no duplicar ni consumir otro cupo
    if plan.meta_campaign_id:
        raise HTTPException(status_code=409, detail=f"Ya publicado. campaign_id: {plan.meta_campaign_id}")

    # Permiso de rol + límite de campañas activas del tier
    if not permissions.can(current_user, "publish_campaign"):
        raise HTTPException(status_code=403, detail=f"Tu rol ({current_user.role}) no permite publicar campañas")
    await permissions.assert_can_publish_campaign(db, current_user)

    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account.id)
    )
    settings = settings_result.scalar_one_or_none()
    if not settings or not settings.meta_access_token or not settings.meta_ad_account_id:
        raise HTTPException(
            status_code=400,
            detail="Configura tu Meta Access Token y Ad Account ID en Ajustes antes de publicar.",
        )

    task_result = await db.execute(
        select(AgentTask).where(
            AgentTask.plan_id == plan_id,
            AgentTask.agent_name == "AdsAgent",
            AgentTask.status == "completed",
        )
    )
    ads_task = task_result.scalar_one_or_none()
    if not ads_task or not ads_task.output:
        raise HTTPException(status_code=400, detail="El AdsAgent aún no ha generado la campaña.")

    campaign_json = ads_task.output.get("campaign_json")
    if not campaign_json:
        raise HTTPException(status_code=400, detail="No hay campaign_json en el output del AdsAgent.")

    _objective_map = {
        "LEAD_GENERATION": "OUTCOME_LEADS",
        "CONVERSIONS": "OUTCOME_SALES",
        "TRAFFIC": "OUTCOME_TRAFFIC",
        "BRAND_AWARENESS": "OUTCOME_AWARENESS",
        "REACH": "OUTCOME_AWARENESS",
        "ENGAGEMENT": "OUTCOME_ENGAGEMENT",
        "APP_INSTALLS": "OUTCOME_APP_PROMOTION",
    }
    if "campaign" in campaign_json:
        obj = campaign_json["campaign"].get("objective", "")
        campaign_json["campaign"]["objective"] = _objective_map.get(obj, obj)

    # instant_form: resolver (o auto-crear) el Lead Ad form e inyectar su id en los ads
    if (plan.funnel_type or "") == "instant_form":
        from app.services.lead_forms import resolve_form_id_for_plan
        from app.tools.meta_ads import inject_lead_gen_form_id
        try:
            form_id = await resolve_form_id_for_plan(db, plan, settings)
        except MetaAdsError as e:
            raise HTTPException(status_code=422, detail=str(e))
        if form_id:
            inject_lead_gen_form_id(campaign_json, form_id)

    try:
        result = await publish_campaign(
            access_token=settings.meta_access_token,
            ad_account_id=settings.meta_ad_account_id,
            campaign_json=campaign_json,
            dsa_beneficiary=settings.company_name or "Anunciante",
            dsa_payor=settings.company_name or "Anunciante",
            page_id=settings.meta_page_id or "",
        )
    except MetaAdsError as e:
        raise HTTPException(status_code=502, detail=f"Error Meta API: {e}")

    plan.meta_campaign_id = result["campaign_id"]

    # Multi-Angle: mapear los ad_set_id reales de Meta a cada ángulo. El orden de
    # publicación es [ad_set_id] + additional_ad_set_ids, alineado con angles_tested.
    # Sin esto, el sync de métricas por ángulo y la redistribución no encuentran sus ad sets.
    if (plan.ab_mode or "ab_classic") == "multi_angle" and plan.angles_tested:
        adset_ids = [result.get("ad_set_id")] + list(result.get("additional_ad_set_ids") or [])
        angles = [dict(a) for a in plan.angles_tested]
        for angle, asid in zip(angles, adset_ids):
            if asid:
                angle["ad_set_id"] = str(asid)
        plan.angles_tested = angles
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(plan, "angles_tested")

    await db.commit()

    # Kick inicial del sync de métricas (el resto lo hace el beat horario)
    try:
        from app.workers.metrics_tasks import sync_metrics_for_plan
        sync_metrics_for_plan.delay(str(plan.id))
    except Exception:
        pass

    return PublishResult(**result)


# ─── Meta Insights ────────────────────────────────────────────────────────────

@router.get("/{plan_id}/meta-insights", response_model=MetaInsights)
async def get_meta_insights(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> MetaInsights:
    plan_result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = plan_result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if not plan.meta_campaign_id:
        raise HTTPException(status_code=404, detail="Este plan no tiene campaña publicada en Meta")

    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account.id)
    )
    settings = settings_result.scalar_one_or_none()
    if not settings or not settings.meta_access_token:
        raise HTTPException(status_code=400, detail="Meta Access Token no configurado")

    # Caché 15 min — evita pegar a Meta en cada carga del dashboard (rate limits)
    from app.services.cache import cache_get, cache_set
    cache_key = f"insights:{plan.meta_campaign_id}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return MetaInsights(**cached)

    try:
        data = await get_campaign_insights(settings.meta_access_token, plan.meta_campaign_id)
    except MetaAdsError as e:
        raise HTTPException(status_code=502, detail=f"Error Meta API: {e}")

    if data:
        await cache_set(cache_key, data, ttl_seconds=900)
    return MetaInsights(**data) if data else MetaInsights()


# ─── Funnel metrics ──────────────────────────────────────────────────────────

@router.get("/{plan_id}/metrics", response_model=FunnelMetrics)
async def get_funnel_metrics(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> FunnelMetrics:
    plan = (await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    leads = (await db.execute(
        select(Lead).where(Lead.plan_id == plan_id)
    )).scalars().all()

    total = len(leads)
    contacted = sum(1 for l in leads if l.lead_status in ("contacted", "showed_up", "closed", "lost"))
    showed_up = sum(1 for l in leads if l.lead_status in ("showed_up", "closed"))
    closed = sum(1 for l in leads if l.lead_status == "closed")
    lost = sum(1 for l in leads if l.lead_status == "lost")

    revenue = sum(float(l.closed_value) for l in leads if l.closed_value is not None)

    total_spent = 0.0
    if plan.meta_campaign_id:
        settings = (await db.execute(
            select(UserSettings).where(UserSettings.client_account_id == client_account.id)
        )).scalar_one_or_none()
        if settings and settings.meta_access_token:
            try:
                from app.tools.meta_ads import get_campaign_insights
                data = await get_campaign_insights(settings.meta_access_token, plan.meta_campaign_id)
                total_spent = float(data.get("spend", 0) or 0)
            except Exception:
                pass

    cpl_real = (total_spent / total) if total and total_spent else None
    cost_per_show_up = (total_spent / showed_up) if showed_up and total_spent else None
    cost_per_close = (total_spent / closed) if closed and total_spent else None
    roas = (revenue / total_spent) if total_spent and revenue else None
    avg_closed_value = (revenue / closed) if closed else None

    return FunnelMetrics(
        total_leads=total,
        contacted=contacted,
        showed_up=showed_up,
        closed=closed,
        lost=lost,
        total_spent=total_spent,
        revenue_attributed=revenue,
        cpl_real=cpl_real,
        cost_per_show_up=cost_per_show_up,
        cost_per_close=cost_per_close,
        roas=roas,
        avg_closed_value=avg_closed_value,
    )


# ─── Leads extendido — incluye estado de secuencia + acción recomendada ──────

@router.get("/{plan_id}/leads", response_model=list[LeadDetail])
async def get_campaign_leads(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[LeadDetail]:
    plan_result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    if not plan_result.scalar_one_or_none():
        return []

    # Orden: pendientes primero (action_completed_at NULL), luego por score desc,
    # luego por fecha desc. Los marcados como hechos van al final.
    leads_result = await db.execute(
        select(Lead)
        .where(Lead.plan_id == plan_id)
        .order_by(
            case((Lead.action_completed_at.is_(None), 0), else_=1).asc(),
            Lead.score.desc().nulls_last(),
            Lead.created_at.desc(),
        )
    )
    leads = leads_result.scalars().all()
    if not leads:
        return []

    lead_ids = [l.id for l in leads]
    events_result = await db.execute(
        select(SequenceEvent)
        .where(SequenceEvent.lead_id.in_(lead_ids))
        .order_by(SequenceEvent.order.asc())
    )
    events = events_result.scalars().all()

    by_lead: dict[uuid.UUID, list[SequenceEvent]] = {}
    for ev in events:
        by_lead.setdefault(ev.lead_id, []).append(ev)

    output: list[LeadDetail] = []
    for lead in leads:
        lead_events = by_lead.get(lead.id, [])
        email_events = [e for e in lead_events if e.channel == "email"]
        wa_events = [e for e in lead_events if e.channel == "whatsapp"]

        sequence_status = _compute_sequence_status(email_events, wa_events)

        output.append(LeadDetail(
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
            sequence_status=sequence_status,
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
                for e in lead_events
            ],
            lead_status=lead.lead_status,
            closed_value=lead.closed_value,
            meeting_scheduled_at=lead.meeting_scheduled_at,
            showed_up_at=lead.showed_up_at,
            closed_at=lead.closed_at,
            created_at=lead.created_at,
        ))

    return output


def _compute_sequence_status(email_events: list, wa_events: list) -> dict:
    """Compute current position in nurturing sequence + next event ETA."""
    def channel_stats(events: list) -> dict:
        total = len(events)
        sent = sum(1 for e in events if e.status == "sent")
        failed = sum(1 for e in events if e.status == "failed")
        skipped = sum(1 for e in events if e.status == "skipped")
        next_ev = next(
            (e for e in events if e.status == "scheduled"),
            None,
        )
        return {
            "total": total,
            "sent": sent,
            "failed": failed,
            "skipped": skipped,
            "next_order": next_ev.order if next_ev else None,
            "next_subject": next_ev.subject if next_ev else None,
            "next_at": next_ev.scheduled_at.isoformat() if next_ev and next_ev.scheduled_at else None,
        }

    return {
        "email": channel_stats(email_events),
        "whatsapp": channel_stats(wa_events),
    }


# ─── Acciones por lead: marcar hecho / pendiente ──────────────────────────────

class LeadActionUpdate(BaseModel):
    completed: bool
    note: str | None = None


@router.patch("/{plan_id}/leads/{lead_id}/action", response_model=LeadDetail)
async def toggle_lead_action(
    plan_id: uuid.UUID,
    lead_id: uuid.UUID,
    body: LeadActionUpdate,
    current_user: User = Depends(permissions.require_action("edit_leads")),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> LeadDetail:
    # Verificar plan pertenece al usuario
    plan_result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    if not plan_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Plan not found")

    lead = (await db.execute(
        select(Lead).where(Lead.id == lead_id, Lead.plan_id == plan_id)
    )).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.action_completed_at = datetime.now(timezone.utc) if body.completed else None
    if body.note is not None:
        lead.action_note = body.note or None

    await db.commit()
    await db.refresh(lead)

    # Devolver con sequence_status para que el frontend pueda mergear
    events = (await db.execute(
        select(SequenceEvent).where(SequenceEvent.lead_id == lead.id).order_by(SequenceEvent.order.asc())
    )).scalars().all()
    email_events = [e for e in events if e.channel == "email"]
    wa_events = [e for e in events if e.channel == "whatsapp"]
    seq_status = _compute_sequence_status(email_events, wa_events)

    return LeadDetail(
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
