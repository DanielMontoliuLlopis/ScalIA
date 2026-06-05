import uuid
from datetime import datetime

import enum

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PlanStatus(str, enum.Enum):
    pending_approval = "pending_approval"
    approved = "approved"
    rejected = "rejected"
    executing = "executing"
    awaiting_creative_choice = "awaiting_creative_choice"
    pending_copy_approval = "pending_copy_approval"
    awaiting_funnel_choice = "awaiting_funnel_choice"
    pending_ads_approval = "pending_ads_approval"
    research_view = "research_view"
    done = "done"


class AbMode(str, enum.Enum):
    ab_classic = "ab_classic"
    multi_angle = "multi_angle"


class CreativeType(str, enum.Enum):
    image_ai = "image_ai"
    image_upload = "image_upload"
    video_upload = "video_upload"
    reel_upload = "reel_upload"
    meta_post = "meta_post"


class FunnelType(str, enum.Enum):
    instant_form = "instant_form"
    landing_direct = "landing_direct"
    landing_lm = "landing_lm"
    landing_lm_direct = "landing_lm_direct"


class SaleType(str, enum.Enum):
    call = "call"
    payment = "payment"


class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    steps: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default=PlanStatus.pending_approval)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_campaign_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    funnel_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    sale_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    redirect_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    creative_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Lead Ad form (instant_form): plantilla seleccionada por el usuario; si null y el
    # funnel es instant_form, se auto-crea un form por defecto al publicar.
    lead_form_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lead_forms.id"), nullable=True
    )
    creative_a: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    creative_b: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ab_testing: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Multi-Angle Testing (MAT)
    ab_mode: Mapped[str] = mapped_column(String(20), nullable=False, default=AbMode.ab_classic)
    num_angles: Mapped[int | None] = mapped_column(Integer, nullable=True)
    angles_tested: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    # Research Export Mode
    research_export: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    export_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Offer Engine fields
    precio_base: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    tipo_oferta: Mapped[str | None] = mapped_column(String(30), nullable=True)
    urgencia: Mapped[str | None] = mapped_column(String(50), nullable=True)
    garantia: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transformacion: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Offer Testing fields
    parent_plan_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=True)
    is_offer_test: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    offer_test_label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
