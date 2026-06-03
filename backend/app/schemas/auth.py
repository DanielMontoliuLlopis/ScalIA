import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

BusinessType = Literal["saas", "ecommerce", "services", "app", "local"]
PlanTier = Literal["trial", "starter", "growth", "agency"]
TeamRole = Literal["owner", "admin", "member", "viewer"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    business_type: BusinessType | None = None
    # Código de referido del closer (link /?ref=CODE). Opcional.
    ref_code: str | None = Field(default=None, max_length=40)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None = None
    phone: str | None = None
    business_type: str | None = None
    plan: str
    role: str
    is_founder: bool = False
    is_superadmin: bool = False
    active_campaigns_limit: int
    subscription_status: str | None = None
    subscription_current_period_end: datetime | None = None
    stripe_customer_id: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
