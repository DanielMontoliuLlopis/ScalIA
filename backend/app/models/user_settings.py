import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # user_id se conserva como referencia de auditoría; el scope real es client_account_id
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, unique=True, index=True
    )
    meta_pixel_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    meta_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta_ad_account_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color_palette: Mapped[str] = mapped_column(String(20), nullable=False, default="indigo")
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    business_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    resend_api_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    resend_from_email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    meta_page_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # URL de política de privacidad — obligatoria para crear Lead Ad forms en Meta.
    # Sirve de fallback al auto-crear el formulario de una campaña instant_form.
    privacy_policy_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    whatsapp_phone_number_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    whatsapp_phone_display: Mapped[str | None] = mapped_column(String(30), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
