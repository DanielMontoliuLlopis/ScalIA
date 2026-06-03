import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, ForeignKey, func
# hero_image_url uses Text to support base64 data URLs
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LandingPage(Base):
    __tablename__ = "landing_pages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True
    )
    variant: Mapped[str] = mapped_column(String(1), nullable=False, default="a")
    campaign_type: Mapped[str] = mapped_column(String(20), nullable=False, default="lead_gen")
    # campaign_type values: lead_gen | direct_sale | validation
    funnel_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # funnel_type values: instant_form | landing_direct | landing_lm | landing_lm_direct
    landing_subtype: Mapped[str | None] = mapped_column(String(10), nullable=True)
    # landing_subtype: lm (captura) | sale (venta) | null (legacy)
    sale_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # sale_type: call | payment | null
    headline: Mapped[str] = mapped_column(String(300), nullable=False)
    subheadline: Mapped[str] = mapped_column(String(500), nullable=False)
    benefits: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    cta_text: Mapped[str] = mapped_column(String(100), nullable=False)
    hero_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    primary_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#6366f1")
    secondary_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#e0e7ff")
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    meta_pixel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    redirect_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    form_fields: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    sale_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    template_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    conversions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
