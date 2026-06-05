import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LeadForm(Base):
    """Formulario de Lead Ad (instant_form) reutilizable.

    Plantilla gestionable desde la plataforma. Al sincronizar se crea en la Page
    de Meta y se guarda `meta_form_id`. Una campaña instant_form referencia un
    LeadForm (o se auto-crea uno por defecto al publicar)."""

    __tablename__ = "lead_forms"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    client_account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("client_accounts.id"), nullable=False, index=True
    )
    # creador (auditoría); el scope real es client_account_id
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    locale: Mapped[str] = mapped_column(String(10), nullable=False, default="es_ES")

    # Tarjeta de introducción (context card)
    intro_headline: Mapped[str | None] = mapped_column(String(300), nullable=True)
    intro_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Campos del formulario. Lista ordenada de preguntas:
    #   prefill: {"type": "prefill", "key": "EMAIL"|"FULL_NAME"|"PHONE"|"COMPANY_NAME"|"JOB_TITLE"|"CITY", "label": str}
    #   custom:  {"type": "custom", "key": "q1", "label": str, "format": "text"|"select", "options": [str]}
    fields: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)

    # Política de privacidad (obligatoria para Meta)
    privacy_policy_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    privacy_policy_link_text: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Página de agradecimiento
    thank_you_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    thank_you_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    thank_you_button_text: Mapped[str | None] = mapped_column(String(100), nullable=True)
    # VIEW_WEBSITE | DOWNLOAD | CALL_BUSINESS
    thank_you_button_type: Mapped[str] = mapped_column(String(30), nullable=False, default="VIEW_WEBSITE")
    thank_you_website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Sincronización con Meta
    meta_form_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    meta_page_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
