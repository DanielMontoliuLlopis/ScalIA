import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


# ── Overview ──────────────────────────────────────────────────────────────────
class AdminOverview(BaseModel):
    total_users: int
    active_subscriptions: int
    mrr_cents: int                      # MRR aproximado en céntimos
    currency: str
    total_closers: int
    active_closers: int
    commissions_pending_cents: int
    commissions_paid_cents: int


# ── Closers ───────────────────────────────────────────────────────────────────
class CloserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    commission_rate: Decimal = Field(default=Decimal("0.06"), ge=0, le=1)
    # Si se omite, se genera una contraseña temporal y se devuelve una sola vez.
    password: str | None = Field(default=None, min_length=8, max_length=128)


class CloserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=200)
    phone: str | None = Field(default=None, max_length=50)
    commission_rate: Decimal | None = Field(default=None, ge=0, le=1)
    is_active: bool | None = None


class CloserRow(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    phone: str | None = None
    commission_rate: Decimal
    referral_code: str
    is_active: bool
    clients_count: int = 0
    commissions_pending_cents: int = 0
    commissions_paid_cents: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Clientes ──────────────────────────────────────────────────────────────────
class AdminClientRow(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None = None
    plan: str
    subscription_status: str | None = None
    is_founder: bool = False
    closer_id: uuid.UUID | None = None
    closer_name: str | None = None
    mrr_cents: int = 0
    created_at: datetime


class AssignCloserRequest(BaseModel):
    closer_id: uuid.UUID | None = None   # None = quitar atribución


# ── Comisiones ────────────────────────────────────────────────────────────────
class CommissionRow(BaseModel):
    id: uuid.UUID
    closer_id: uuid.UUID
    closer_name: str | None = None
    user_id: uuid.UUID
    client_email: str | None = None
    stripe_invoice_id: str
    type: Literal["first_quota", "recurring"]
    base_amount: Decimal
    commission_amount: Decimal
    currency: str
    period_start: datetime | None = None
    status: Literal["pending", "paid"]
    paid_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class LiquidateRequest(BaseModel):
    commission_ids: list[uuid.UUID] = Field(min_length=1)


class LiquidateResponse(BaseModel):
    liquidated: int
    total_cents: int


class CloserDetail(BaseModel):
    closer: CloserRow
    clients: list[AdminClientRow]
    commissions: list[CommissionRow]


class CloserCreated(CloserRow):
    # Contraseña en claro mostrada UNA sola vez al crear (o resetear).
    temp_password: str | None = None


class ResetPasswordResponse(BaseModel):
    temp_password: str
