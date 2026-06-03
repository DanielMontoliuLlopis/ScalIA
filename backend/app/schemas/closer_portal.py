import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class CloserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class CloserTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CloserMe(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    commission_rate: float
    referral_code: str
    is_active: bool


class MonthlyCommission(BaseModel):
    month: str                  # "2026-05"
    label: str                  # "May 2026"
    count: int
    first_quota_cents: int
    recurring_cents: int
    total_cents: int
    pending_cents: int
    paid_cents: int


class CloserDashboard(BaseModel):
    currency: str
    clients_count: int
    active_clients_count: int
    total_earned_cents: int       # todas las comisiones (pending + paid)
    pending_cents: int
    paid_cents: int
    months: list[MonthlyCommission]
