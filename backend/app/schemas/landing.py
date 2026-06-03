import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class FormField(BaseModel):
    name: str
    label: str
    type: str = "text"
    required: bool
    placeholder: str = ""
    options: list[str] | None = None
    helper: str | None = None


class LandingPageResponse(BaseModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    user_id: uuid.UUID
    variant: str
    campaign_type: str
    headline: str
    subheadline: str
    benefits: list[str]
    cta_text: str
    hero_image_url: str | None = None
    primary_color: str
    secondary_color: str
    logo_url: str | None = None
    meta_pixel_id: str | None = None
    redirect_url: str | None = None
    form_fields: list[Any]
    sale_content: dict[str, Any] | None = None
    landing_subtype: str | None = None
    sale_type: str | None = None
    funnel_type: str | None = None
    template_id: str | None = None
    views: int
    conversions: int
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LandingPageUpdate(BaseModel):
    headline: str | None = None
    subheadline: str | None = None
    benefits: list[str] | None = None
    cta_text: str | None = None
    redirect_url: str | None = None
    sale_content: dict[str, Any] | None = None


class LeadSubmit(BaseModel):
    email: str
    nombre: str | None = None
    empresa: str | None = None
    telefono: str | None = None
    num_empleados: str | None = None
    extra_data: dict = {}


class LeadResponse(BaseModel):
    id: uuid.UUID
    email: str
    nombre: str | None = None
    empresa: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
