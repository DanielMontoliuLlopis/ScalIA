from typing import Literal

from pydantic import BaseModel

Tier = Literal["starter", "growth", "agency"]
CheckoutTier = Literal["starter", "growth", "agency", "research_10", "research_100"]


class CheckoutRequest(BaseModel):
    plan: CheckoutTier
    founder: bool = False


class CheckoutResponse(BaseModel):
    url: str


class PortalResponse(BaseModel):
    url: str


class PlanInfo(BaseModel):
    id: Tier
    name: str
    amount: int               # precio normal (céntimos)
    founder_amount: int       # precio fundador de por vida (céntimos)
    currency: str
    interval: str = "month"
    trial_days: int
    active_campaigns_limit: int
    team_seats: int
    features: list[str]


class FounderStatus(BaseModel):
    spots_total: int
    spots_taken: int
    spots_left: int
    is_open: bool
