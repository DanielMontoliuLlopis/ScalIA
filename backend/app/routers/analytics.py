import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_active_client_account, get_current_user
from app.database import get_db
from app.models.client_account import ClientAccount
from app.models.landing_page import LandingPage
from app.models.lead import Lead
from app.models.plan import Plan
from app.models.user import User
from app.models.user_settings import UserSettings
from app.tools.meta_ads import get_campaign_insights, MetaAdsError

router = APIRouter(prefix="/analytics", tags=["analytics"])


class CampaignAnalytics(BaseModel):
    plan_id: uuid.UUID
    title: str
    status: str
    meta_campaign_id: str | None = None
    total_leads: int = 0
    contacted: int = 0
    showed_up: int = 0
    closed: int = 0
    lost: int = 0
    total_spent: float = 0.0
    revenue_attributed: float = 0.0
    cpl_real: float | None = None
    cost_per_show_up: float | None = None
    cost_per_close: float | None = None
    roas: float | None = None
    avg_closed_value: float | None = None
    # Meta Insights
    impressions: int = 0
    clicks: int = 0
    meta_spend: float = 0.0
    reach: int = 0
    cpc: float | None = None
    ctr: float | None = None
    meta_leads: int = 0
    created_at: datetime


class OverviewAnalytics(BaseModel):
    active_campaigns: int = 0
    total_leads: int = 0
    total_showed_up: int = 0
    total_closed: int = 0
    total_revenue: float = 0.0
    total_spent: float = 0.0
    avg_cpl: float | None = None
    avg_roas: float | None = None
    campaigns: list[CampaignAnalytics] = []


ACTIVE_STATUSES = {"executing", "pending_ads_approval", "done", "pending_copy_approval"}


@router.get("/overview", response_model=OverviewAnalytics)
async def get_overview(
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> OverviewAnalytics:
    plans_result = await db.execute(
        select(Plan).where(
            Plan.client_account_id == client_account.id,
            Plan.status.in_(ACTIVE_STATUSES),
        ).order_by(Plan.created_at.desc())
    )
    plans = plans_result.scalars().all()

    settings_result = await db.execute(
        select(UserSettings).where(UserSettings.client_account_id == client_account.id)
    )
    settings = settings_result.scalar_one_or_none()

    campaign_list: list[CampaignAnalytics] = []

    for plan in plans:
        # DB metrics from leads
        leads_result = await db.execute(
            select(Lead).where(Lead.plan_id == plan.id, Lead.client_account_id == client_account.id)
        )
        leads = leads_result.scalars().all()

        total_leads = len(leads)
        contacted = sum(1 for l in leads if l.lead_status in ("contacted", "showed_up", "closed"))
        showed_up = sum(1 for l in leads if l.lead_status in ("showed_up", "closed"))
        closed = sum(1 for l in leads if l.lead_status == "closed")
        lost = sum(1 for l in leads if l.lead_status == "lost")
        revenue = float(sum(l.closed_value or 0 for l in leads))

        # Meta Insights
        impressions = clicks = reach = meta_leads = 0
        meta_spend = cpc = ctr = None
        if plan.meta_campaign_id and settings and settings.meta_access_token:
            try:
                data = await get_campaign_insights(settings.meta_access_token, plan.meta_campaign_id)
                if data:
                    impressions = data.get("impressions", 0)
                    clicks = data.get("clicks", 0)
                    reach = data.get("reach", 0)
                    meta_spend = data.get("spend", 0.0)
                    meta_leads = data.get("leads", 0)
                    cpc = data.get("cpc")
                    ctr = data.get("ctr")
            except MetaAdsError:
                pass

        total_spent = float(meta_spend or 0.0)
        cpl_real = (total_spent / total_leads) if total_leads > 0 and total_spent > 0 else None
        cost_per_show_up = (total_spent / showed_up) if showed_up > 0 and total_spent > 0 else None
        cost_per_close = (total_spent / closed) if closed > 0 and total_spent > 0 else None
        roas = (revenue / total_spent) if total_spent > 0 else None
        avg_closed_value = (revenue / closed) if closed > 0 else None

        campaign_list.append(CampaignAnalytics(
            plan_id=plan.id,
            title=plan.title,
            status=plan.status,
            meta_campaign_id=plan.meta_campaign_id,
            total_leads=total_leads,
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
            impressions=impressions,
            clicks=clicks,
            meta_spend=float(meta_spend or 0),
            reach=reach,
            cpc=cpc,
            ctr=ctr,
            meta_leads=meta_leads,
            created_at=plan.created_at,
        ))

    # Aggregate totals
    all_leads = sum(c.total_leads for c in campaign_list)
    all_showed_up = sum(c.showed_up for c in campaign_list)
    all_closed = sum(c.closed for c in campaign_list)
    all_revenue = sum(c.revenue_attributed for c in campaign_list)
    all_spent = sum(c.total_spent for c in campaign_list)
    avg_cpl = (all_spent / all_leads) if all_leads > 0 and all_spent > 0 else None
    avg_roas = (all_revenue / all_spent) if all_spent > 0 else None

    return OverviewAnalytics(
        active_campaigns=len(campaign_list),
        total_leads=all_leads,
        total_showed_up=all_showed_up,
        total_closed=all_closed,
        total_revenue=all_revenue,
        total_spent=all_spent,
        avg_cpl=avg_cpl,
        avg_roas=avg_roas,
        campaigns=sorted(campaign_list, key=lambda c: c.roas or 0, reverse=True),
    )


# ── Multi-Angle: métricas por ángulo + histórico ────────────────────────────

class AngleMetric(BaseModel):
    angle: str
    hook: str | None = None
    image_url: str | None = None
    status: str = "active"
    budget_share: float | None = None
    impressions: int = 0
    clicks: int = 0
    leads: int = 0
    spend: float = 0.0
    ctr: float | None = None
    cpl: float | None = None
    roas: float | None = None


class AnglePerformanceRow(BaseModel):
    id: uuid.UUID
    business_type: str
    angle: str
    tipo_oferta: str | None = None
    impressions: int
    clicks: int
    leads: int
    spend: float
    ctr: float | None = None
    cpl: float | None = None
    roas: float | None = None
    result: str
    period_start: datetime
    period_end: datetime | None = None

    model_config = {"from_attributes": True}


@router.get("/campaign/{plan_id}/angles", response_model=list[AngleMetric])
async def get_campaign_angles(
    plan_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[AngleMetric]:
    """Rendimiento por ángulo de una campaña multi_angle (desde plan.angles_tested)."""
    result = await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    angles = plan.angles_tested or []
    out: list[AngleMetric] = []
    for a in angles:
        impressions = int(a.get("impressions") or 0)
        clicks = int(a.get("clicks") or 0)
        leads = int(a.get("leads") or 0)
        spend = float(a.get("spend") or 0)
        out.append(AngleMetric(
            angle=a.get("angle", ""),
            hook=a.get("hook"),
            image_url=a.get("image_url"),
            status=a.get("status", "active"),
            budget_share=a.get("budget_share"),
            impressions=impressions,
            clicks=clicks,
            leads=leads,
            spend=spend,
            ctr=(clicks / impressions * 100) if impressions else a.get("ctr"),
            cpl=(spend / leads) if leads else a.get("cpl"),
            roas=a.get("roas"),
        ))
    return out


@router.get("/angle-performance", response_model=list[AnglePerformanceRow])
async def angle_performance(
    business_type: str | None = None,
    angle: str | None = None,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[Any]:
    """Histórico de rendimiento por ángulo (agregado por cuenta/agencia)."""
    from app.models.angle_performance import AnglePerformance
    from app.services.permissions import account_owner_id

    owner_id = account_owner_id(current_user)
    conds = [
        (AnglePerformance.user_id == current_user.id)
        | (AnglePerformance.account_id == owner_id)
    ]
    if business_type:
        conds.append(AnglePerformance.business_type == business_type)
    if angle:
        conds.append(AnglePerformance.angle == angle)
    rows = await db.execute(
        select(AnglePerformance).where(*conds).order_by(AnglePerformance.created_at.desc())
    )
    return rows.scalars().all()


class TimeseriesPoint(BaseModel):
    date: str
    impressions: int = 0
    clicks: int = 0
    reach: int = 0
    leads: int = 0
    conversions: int = 0
    spend: float = 0.0
    revenue: float = 0.0
    ctr: float | None = None
    cpc: float | None = None
    cpm: float | None = None
    cpl: float | None = None


class BreakdownRow(BaseModel):
    value: str
    impressions: int = 0
    clicks: int = 0
    leads: int = 0
    spend: float = 0.0
    revenue: float = 0.0
    ctr: float | None = None
    cpl: float | None = None
    roas: float | None = None


def _derive(impr: int, clicks: int, spend: float, leads: int, revenue: float) -> dict:
    return {
        "ctr": (clicks / impr * 100) if impr else None,
        "cpc": (spend / clicks) if clicks else None,
        "cpm": (spend / impr * 1000) if impr else None,
        "cpl": (spend / leads) if leads else None,
        "roas": (revenue / spend) if spend else None,
    }


class DashboardCampaignRow(BaseModel):
    plan_id: uuid.UUID
    title: str
    status: str
    meta_campaign_id: str | None = None
    impressions: int = 0
    clicks: int = 0
    reach: int = 0
    spend: float = 0.0
    revenue: float = 0.0
    leads: int = 0          # leads capturados (tabla Lead)
    meta_leads: int = 0     # leads atribuidos por Meta (snapshots)
    ctr: float | None = None
    cpl: float | None = None
    roas: float | None = None


class AlertRow(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    plan_title: str | None = None
    type: str
    severity: str
    title: str
    message: str
    metric_key: str
    current_value: float | None = None
    baseline_value: float | None = None
    status: str
    snapshot_date: str
    created_at: datetime


class DashboardAnalytics(BaseModel):
    days: int
    totals: dict[str, Any]
    timeseries: list[TimeseriesPoint] = []
    by_campaign: list[DashboardCampaignRow] = []
    by_placement: list[BreakdownRow] = []
    by_device: list[BreakdownRow] = []
    alerts: list[AlertRow] = []


@router.get("/alerts", response_model=list[AlertRow])
async def list_alerts(
    status: str = "active",
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[AlertRow]:
    from app.models.metric_alert import MetricAlert

    conds = [MetricAlert.client_account_id == client_account.id]
    if status:
        conds.append(MetricAlert.status == status)
    rows = (await db.execute(
        select(MetricAlert, Plan.title)
        .join(Plan, Plan.id == MetricAlert.plan_id)
        .where(*conds)
        .order_by(MetricAlert.created_at.desc())
    )).all()
    return [_alert_row(a, title) for a, title in rows]


@router.post("/alerts/{alert_id}/dismiss", response_model=AlertRow)
async def dismiss_alert(
    alert_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> AlertRow:
    from app.models.metric_alert import MetricAlert

    alert = (await db.execute(
        select(MetricAlert).where(
            MetricAlert.id == alert_id,
            MetricAlert.client_account_id == client_account.id,
        )
    )).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "dismissed"
    await db.commit()
    await db.refresh(alert)
    plan = (await db.execute(select(Plan).where(Plan.id == alert.plan_id))).scalar_one_or_none()
    return _alert_row(alert, plan.title if plan else None)


def _alert_row(a: Any, plan_title: str | None) -> "AlertRow":
    return AlertRow(
        id=a.id, plan_id=a.plan_id, plan_title=plan_title,
        type=a.type, severity=a.severity, title=a.title, message=a.message,
        metric_key=a.metric_key,
        current_value=float(a.current_value) if a.current_value is not None else None,
        baseline_value=float(a.baseline_value) if a.baseline_value is not None else None,
        status=a.status, snapshot_date=a.snapshot_date.isoformat(), created_at=a.created_at,
    )


@router.get("/dashboard", response_model=DashboardAnalytics)
async def get_dashboard(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> DashboardAnalytics:
    """Dashboard global en UNA sola llamada, leyendo de metric_snapshots (no Meta).

    Sustituye el patrón antiguo (1 + N llamadas a Meta Insights en vivo) por
    agregaciones en BD. Los snapshots los mantiene fresco el beat horario.
    """
    from app.models.metric_snapshot import MetricSnapshot

    since = (datetime.now(timezone.utc) - timedelta(days=days)).date()

    # ── Planes activos del account ────────────────────────────────────────────
    plans = (await db.execute(
        select(Plan).where(
            Plan.client_account_id == client_account.id,
            Plan.status.in_(ACTIVE_STATUSES),
        ).order_by(Plan.created_at.desc())
    )).scalars().all()
    plan_by_id = {p.id: p for p in plans}

    # ── Agregado por plan (nivel ad, sin breakdown) ───────────────────────────
    per_plan = (await db.execute(
        select(
            MetricSnapshot.plan_id,
            func.sum(MetricSnapshot.impressions),
            func.sum(MetricSnapshot.clicks),
            func.sum(MetricSnapshot.reach),
            func.sum(MetricSnapshot.leads),
            func.sum(MetricSnapshot.spend),
            func.sum(MetricSnapshot.revenue),
        )
        .where(
            MetricSnapshot.client_account_id == client_account.id,
            MetricSnapshot.level == "ad",
            MetricSnapshot.breakdown_key == "",
            MetricSnapshot.snapshot_date >= since,
        )
        .group_by(MetricSnapshot.plan_id)
    )).all()
    metrics_by_plan = {row[0]: row for row in per_plan}

    # ── Leads capturados (tabla Lead) por plan ────────────────────────────────
    leads_rows = (await db.execute(
        select(Lead.plan_id, func.count())
        .where(Lead.client_account_id == client_account.id)
        .group_by(Lead.plan_id)
    )).all()
    leads_by_plan = {pid: int(cnt or 0) for pid, cnt in leads_rows}

    by_campaign: list[DashboardCampaignRow] = []
    for plan in plans:
        m = metrics_by_plan.get(plan.id)
        impr = int(m[1] or 0) if m else 0
        clicks = int(m[2] or 0) if m else 0
        reach = int(m[3] or 0) if m else 0
        meta_leads = int(m[4] or 0) if m else 0
        spend = float(m[5] or 0) if m else 0.0
        revenue = float(m[6] or 0) if m else 0.0
        captured = leads_by_plan.get(plan.id, 0)
        der = _derive(impr, clicks, spend, max(captured, meta_leads), revenue)
        by_campaign.append(DashboardCampaignRow(
            plan_id=plan.id, title=plan.title, status=plan.status,
            meta_campaign_id=plan.meta_campaign_id,
            impressions=impr, clicks=clicks, reach=reach,
            spend=spend, revenue=revenue,
            leads=captured, meta_leads=meta_leads,
            ctr=der["ctr"], cpl=der["cpl"], roas=der["roas"],
        ))

    # ── Serie temporal global ─────────────────────────────────────────────────
    ts_rows = (await db.execute(
        select(
            MetricSnapshot.snapshot_date,
            func.sum(MetricSnapshot.impressions),
            func.sum(MetricSnapshot.clicks),
            func.sum(MetricSnapshot.reach),
            func.sum(MetricSnapshot.leads),
            func.sum(MetricSnapshot.conversions),
            func.sum(MetricSnapshot.spend),
            func.sum(MetricSnapshot.revenue),
        )
        .where(
            MetricSnapshot.client_account_id == client_account.id,
            MetricSnapshot.level == "ad",
            MetricSnapshot.breakdown_key == "",
            MetricSnapshot.snapshot_date >= since,
        )
        .group_by(MetricSnapshot.snapshot_date)
        .order_by(MetricSnapshot.snapshot_date.asc())
    )).all()
    timeseries: list[TimeseriesPoint] = []
    for d, impr, clicks, reach, leads, conv, spend, revenue in ts_rows:
        impr = int(impr or 0); clicks = int(clicks or 0); leads = int(leads or 0)
        spend = float(spend or 0); revenue = float(revenue or 0)
        der = _derive(impr, clicks, spend, leads, revenue)
        timeseries.append(TimeseriesPoint(
            date=d.isoformat(), impressions=impr, clicks=clicks, reach=int(reach or 0),
            leads=leads, conversions=int(conv or 0), spend=spend, revenue=revenue,
            ctr=der["ctr"], cpc=der["cpc"], cpm=der["cpm"], cpl=der["cpl"],
        ))

    # ── Breakdowns globales (placement + device) ──────────────────────────────
    async def _global_breakdown(key: str) -> list[BreakdownRow]:
        rows = (await db.execute(
            select(
                MetricSnapshot.breakdown_value,
                func.sum(MetricSnapshot.impressions),
                func.sum(MetricSnapshot.clicks),
                func.sum(MetricSnapshot.leads),
                func.sum(MetricSnapshot.spend),
                func.sum(MetricSnapshot.revenue),
            )
            .where(
                MetricSnapshot.client_account_id == client_account.id,
                MetricSnapshot.level == "campaign",
                MetricSnapshot.breakdown_key == key,
                MetricSnapshot.snapshot_date >= since,
            )
            .group_by(MetricSnapshot.breakdown_value)
            .order_by(func.sum(MetricSnapshot.spend).desc())
        )).all()
        out: list[BreakdownRow] = []
        for value, impr, clicks, leads, spend, revenue in rows:
            impr = int(impr or 0); clicks = int(clicks or 0); leads = int(leads or 0)
            spend = float(spend or 0); revenue = float(revenue or 0)
            der = _derive(impr, clicks, spend, leads, revenue)
            out.append(BreakdownRow(
                value=value or "—", impressions=impr, clicks=clicks, leads=leads,
                spend=spend, revenue=revenue, ctr=der["ctr"], cpl=der["cpl"], roas=der["roas"],
            ))
        return out

    by_placement = await _global_breakdown("publisher_platform")
    by_device = await _global_breakdown("impression_device")

    # ── Alertas activas ───────────────────────────────────────────────────────
    from app.models.metric_alert import MetricAlert
    alert_rows = (await db.execute(
        select(MetricAlert, Plan.title)
        .join(Plan, Plan.id == MetricAlert.plan_id)
        .where(
            MetricAlert.client_account_id == client_account.id,
            MetricAlert.status == "active",
        )
        .order_by(MetricAlert.created_at.desc())
    )).all()
    alerts = [_alert_row(a, title) for a, title in alert_rows]

    # ── Totales ───────────────────────────────────────────────────────────────
    t_impr = sum(c.impressions for c in by_campaign)
    t_clicks = sum(c.clicks for c in by_campaign)
    t_reach = sum(c.reach for c in by_campaign)
    t_spend = sum(c.spend for c in by_campaign)
    t_revenue = sum(c.revenue for c in by_campaign)
    t_captured = sum(c.leads for c in by_campaign)
    t_meta_leads = sum(c.meta_leads for c in by_campaign)
    t_der = _derive(t_impr, t_clicks, t_spend, max(t_captured, t_meta_leads), t_revenue)

    totals = {
        "impressions": t_impr,
        "clicks": t_clicks,
        "reach": t_reach,
        "spend": t_spend,
        "revenue": t_revenue,
        "leads": t_captured,
        "meta_leads": t_meta_leads,
        "ctr": t_der["ctr"],
        "cpc": t_der["cpc"],
        "cpm": t_der["cpm"],
        "cpl": t_der["cpl"],
        "roas": t_der["roas"],
        "published_campaigns": sum(1 for c in by_campaign if c.meta_campaign_id),
        "total_campaigns": len(plans),
    }

    return DashboardAnalytics(
        days=days,
        totals=totals,
        timeseries=timeseries,
        by_campaign=sorted(by_campaign, key=lambda c: c.spend, reverse=True),
        by_placement=by_placement,
        by_device=by_device,
        alerts=alerts,
    )


@router.get("/campaign/{plan_id}/timeseries", response_model=list[TimeseriesPoint])
async def campaign_timeseries(
    plan_id: uuid.UUID,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[TimeseriesPoint]:
    """Serie temporal diaria de la campaña (desde metric_snapshots, sin pegar a Meta).

    Agrega los snapshots de nivel `ad` sin breakdown → total de campaña por día.
    """
    from app.models.metric_snapshot import MetricSnapshot

    plan = (await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    since = (datetime.now(timezone.utc) - timedelta(days=days)).date()
    rows = (await db.execute(
        select(
            MetricSnapshot.snapshot_date,
            func.sum(MetricSnapshot.impressions),
            func.sum(MetricSnapshot.clicks),
            func.sum(MetricSnapshot.reach),
            func.sum(MetricSnapshot.leads),
            func.sum(MetricSnapshot.conversions),
            func.sum(MetricSnapshot.spend),
            func.sum(MetricSnapshot.revenue),
        )
        .where(
            MetricSnapshot.plan_id == plan_id,
            MetricSnapshot.level == "ad",
            MetricSnapshot.breakdown_key == "",
            MetricSnapshot.snapshot_date >= since,
        )
        .group_by(MetricSnapshot.snapshot_date)
        .order_by(MetricSnapshot.snapshot_date.asc())
    )).all()

    out: list[TimeseriesPoint] = []
    for d, impr, clicks, reach, leads, conv, spend, revenue in rows:
        impr = int(impr or 0)
        clicks = int(clicks or 0)
        leads = int(leads or 0)
        spend = float(spend or 0)
        revenue = float(revenue or 0)
        der = _derive(impr, clicks, spend, leads, revenue)
        out.append(TimeseriesPoint(
            date=d.isoformat(),
            impressions=impr, clicks=clicks, reach=int(reach or 0),
            leads=leads, conversions=int(conv or 0),
            spend=spend, revenue=revenue,
            ctr=der["ctr"], cpc=der["cpc"], cpm=der["cpm"], cpl=der["cpl"],
        ))
    return out


@router.get("/campaign/{plan_id}/breakdown", response_model=list[BreakdownRow])
async def campaign_breakdown(
    plan_id: uuid.UUID,
    key: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> list[BreakdownRow]:
    """Agregado por dimensión (age, gender, publisher_platform, region,
    impression_device) desde metric_snapshots. Para saber qué segmento convierte."""
    from app.models.metric_snapshot import MetricSnapshot
    from app.tools.meta_ads import SUPPORTED_BREAKDOWNS

    if key not in SUPPORTED_BREAKDOWNS:
        raise HTTPException(status_code=400, detail=f"breakdown no soportado: {key}")

    plan = (await db.execute(
        select(Plan).where(Plan.id == plan_id, Plan.client_account_id == client_account.id)
    )).scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    since = (datetime.now(timezone.utc) - timedelta(days=days)).date()
    rows = (await db.execute(
        select(
            MetricSnapshot.breakdown_value,
            func.sum(MetricSnapshot.impressions),
            func.sum(MetricSnapshot.clicks),
            func.sum(MetricSnapshot.leads),
            func.sum(MetricSnapshot.spend),
            func.sum(MetricSnapshot.revenue),
        )
        .where(
            MetricSnapshot.plan_id == plan_id,
            MetricSnapshot.level == "campaign",
            MetricSnapshot.breakdown_key == key,
            MetricSnapshot.snapshot_date >= since,
        )
        .group_by(MetricSnapshot.breakdown_value)
        .order_by(func.sum(MetricSnapshot.spend).desc())
    )).all()

    out: list[BreakdownRow] = []
    for value, impr, clicks, leads, spend, revenue in rows:
        impr = int(impr or 0)
        clicks = int(clicks or 0)
        leads = int(leads or 0)
        spend = float(spend or 0)
        revenue = float(revenue or 0)
        der = _derive(impr, clicks, spend, leads, revenue)
        out.append(BreakdownRow(
            value=value or "—",
            impressions=impr, clicks=clicks, leads=leads,
            spend=spend, revenue=revenue,
            ctr=der["ctr"], cpl=der["cpl"], roas=der["roas"],
        ))
    return out


@router.get("/angle-performance/summary")
async def angle_performance_summary(
    business_type: str | None = None,
    current_user: User = Depends(get_current_user),
    client_account: ClientAccount = Depends(get_active_client_account),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Win rate por ángulo × business_type."""
    from app.models.angle_performance import AnglePerformance
    from app.services.permissions import account_owner_id

    owner_id = account_owner_id(current_user)
    conds = [
        (AnglePerformance.user_id == current_user.id)
        | (AnglePerformance.account_id == owner_id)
    ]
    if business_type:
        conds.append(AnglePerformance.business_type == business_type)
    rows = await db.execute(
        select(
            AnglePerformance.business_type,
            AnglePerformance.angle,
            func.count().label("total"),
            func.sum(case((AnglePerformance.result == "winner", 1), else_=0)).label("wins"),
        ).where(*conds).group_by(AnglePerformance.business_type, AnglePerformance.angle)
    )
    summary: dict[str, list] = {}
    for bt, ang, total, wins in rows:
        total = int(total or 0)
        wins = int(wins or 0)
        summary.setdefault(bt, []).append({
            "angle": ang,
            "total": total,
            "wins": wins,
            "win_rate": round(wins / total * 100) if total else 0,
        })
    for bt in summary:
        summary[bt].sort(key=lambda x: x["win_rate"], reverse=True)
    return {"by_business_type": summary}
