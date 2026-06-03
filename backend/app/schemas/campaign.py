import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel


class LandingSummary(BaseModel):
    id: uuid.UUID
    variant: str
    headline: str
    subheadline: str | None = None
    benefits: list[str] = []
    cta_text: str | None = None
    hero_image_url: str | None = None
    primary_color: str
    views: int
    conversions: int

    model_config = {"from_attributes": True}


class LeadDetail(BaseModel):
    id: uuid.UUID
    email: str
    nombre: str | None = None
    empresa: str | None = None
    telefono: str | None = None
    num_empleados: str | None = None
    score: int | None = None
    segment: str | None = None
    recommended_action: dict[str, Any] | None = None
    action_completed_at: datetime | None = None
    action_note: str | None = None
    scoring_breakdown: dict[str, Any] | None = None
    extra_data: dict[str, Any] = {}
    sequence_status: dict[str, Any] | None = None
    sequence_events: list[dict[str, Any]] = []
    lead_status: str = "new"
    closed_value: Decimal | None = None
    meeting_scheduled_at: datetime | None = None
    showed_up_at: datetime | None = None
    closed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class FunnelMetrics(BaseModel):
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


class PublishResult(BaseModel):
    campaign_id: str
    ad_set_id: str
    ad_ids: list[str]
    meta_ads_manager_url: str


class MetaInsights(BaseModel):
    impressions: int = 0
    clicks: int = 0
    spend: float = 0.0
    reach: int = 0
    cpc: float | None = None
    ctr: float | None = None
    cpp: float | None = None
    leads: int = 0


class CampaignSummary(BaseModel):
    plan_id: uuid.UUID
    title: str
    status: str
    created_at: datetime
    meta_campaign_id: str | None = None
    # Métricas agregadas
    total_views: int
    total_conversions: int
    total_leads: int
    # Landings
    landings: list[LandingSummary]
    # AdsAgent output (presupuesto, intereses, JSON campaña)
    ads_output: dict[str, Any] | None = None
    # Copy output (para email sequence mock)
    copy_output: dict[str, Any] | None = None
    # EmailAgent output (email_sequence + whatsapp_sequence + thanks_page)
    email_output: dict[str, Any] | None = None
    # Offer Testing
    parent_plan_id: uuid.UUID | None = None
    is_offer_test: bool = False
    offer_test_label: str | None = None
    # Multi-Angle Testing
    ab_mode: str = "ab_classic"
