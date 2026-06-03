import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ClientAccountResponse(BaseModel):
    id: uuid.UUID
    name: str
    logo_url: str | None = None
    business_type: str | None = None
    color_palette: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ClientAccountCreate(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    business_type: str | None = None
    logo_url: str | None = None
    color_palette: str = "indigo"


class ClientAccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    business_type: str | None = None
    logo_url: str | None = None
    color_palette: str | None = None


class ClientMemberResponse(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str | None = None
    role: str

    model_config = {"from_attributes": True}


class AddMemberRequest(BaseModel):
    user_id: uuid.UUID
    role: str = "member"
