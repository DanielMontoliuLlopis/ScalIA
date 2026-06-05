import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# Campos estándar de prefill que Meta reconoce (autocompletados con datos del perfil)
PREFILL_KEYS = {
    "FULL_NAME", "FIRST_NAME", "LAST_NAME", "EMAIL", "PHONE",
    "COMPANY_NAME", "JOB_TITLE", "CITY", "PROVINCE", "COUNTRY", "ZIP",
}


class LeadFormField(BaseModel):
    type: Literal["prefill", "custom"]
    key: str = Field(..., max_length=60)
    label: str = Field(..., max_length=200)
    # solo para custom
    format: Literal["text", "select"] = "text"
    options: list[str] = Field(default_factory=list)


class LeadFormBase(BaseModel):
    name: str = Field(..., max_length=200)
    locale: str = Field(default="es_ES", max_length=10)
    intro_headline: str | None = Field(default=None, max_length=300)
    intro_description: str | None = None
    fields: list[LeadFormField] = Field(default_factory=list)
    privacy_policy_url: str | None = Field(default=None, max_length=500)
    privacy_policy_link_text: str | None = Field(default=None, max_length=200)
    thank_you_title: str | None = Field(default=None, max_length=300)
    thank_you_body: str | None = None
    thank_you_button_text: str | None = Field(default=None, max_length=100)
    thank_you_button_type: Literal["VIEW_WEBSITE", "DOWNLOAD", "CALL_BUSINESS"] = "VIEW_WEBSITE"
    thank_you_website_url: str | None = Field(default=None, max_length=500)


class LeadFormCreate(LeadFormBase):
    pass


class LeadFormUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    locale: str | None = Field(default=None, max_length=10)
    intro_headline: str | None = Field(default=None, max_length=300)
    intro_description: str | None = None
    fields: list[LeadFormField] | None = None
    privacy_policy_url: str | None = Field(default=None, max_length=500)
    privacy_policy_link_text: str | None = Field(default=None, max_length=200)
    thank_you_title: str | None = Field(default=None, max_length=300)
    thank_you_body: str | None = None
    thank_you_button_text: str | None = Field(default=None, max_length=100)
    thank_you_button_type: Literal["VIEW_WEBSITE", "DOWNLOAD", "CALL_BUSINESS"] | None = None
    thank_you_website_url: str | None = Field(default=None, max_length=500)


class LeadFormResponse(LeadFormBase):
    id: uuid.UUID
    meta_form_id: str | None = None
    meta_page_id: str | None = None
    synced_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
