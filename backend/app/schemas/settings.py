import uuid
from datetime import datetime

from pydantic import BaseModel


class UserSettingsUpdate(BaseModel):
    meta_pixel_id: str | None = None
    meta_access_token: str | None = None
    meta_ad_account_id: str | None = None
    color_palette: str | None = None
    logo_url: str | None = None
    company_name: str | None = None
    business_description: str | None = None
    business_type: str | None = None
    resend_api_key: str | None = None
    resend_from_email: str | None = None
    privacy_policy_url: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_phone_display: str | None = None


class UserSettingsResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    client_account_id: uuid.UUID
    meta_pixel_id: str | None = None
    meta_ad_account_id: str | None = None
    color_palette: str
    logo_url: str | None = None
    company_name: str | None = None
    business_description: str | None = None
    business_type: str | None = None
    resend_from_email: str | None = None
    privacy_policy_url: str | None = None
    has_resend_key: bool = False
    has_meta_token: bool = False
    whatsapp_phone_number_id: str | None = None
    whatsapp_phone_display: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
