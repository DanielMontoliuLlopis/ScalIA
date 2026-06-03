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
