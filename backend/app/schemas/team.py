import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

InviteRole = Literal["admin", "member", "viewer"]


class TeamMember(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None = None
    role: str
    is_owner: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteMemberRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=200)
    password: str = Field(min_length=8)
    role: InviteRole = "member"


class UpdateRoleRequest(BaseModel):
    role: InviteRole


class TeamInfo(BaseModel):
    members: list[TeamMember]
    seats_used: int
    seats_limit: int
