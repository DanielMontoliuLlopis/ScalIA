"""landing_pages, leads, user_settings

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-21
"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_settings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, unique=True),
        sa.Column("meta_pixel_id", sa.String(100), nullable=True),
        sa.Column("meta_access_token", sa.Text, nullable=True),
        sa.Column("meta_ad_account_id", sa.String(100), nullable=True),
        sa.Column("color_palette", sa.String(20), nullable=False, server_default="indigo"),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("company_name", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "landing_pages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("variant", sa.String(1), nullable=False, server_default="a"),
        sa.Column("campaign_type", sa.String(20), nullable=False, server_default="lead_gen"),
        sa.Column("headline", sa.String(300), nullable=False),
        sa.Column("subheadline", sa.String(500), nullable=False),
        sa.Column("benefits", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("cta_text", sa.String(100), nullable=False),
        sa.Column("hero_image_url", sa.String(500), nullable=True),
        sa.Column("primary_color", sa.String(7), nullable=False, server_default="#6366f1"),
        sa.Column("secondary_color", sa.String(7), nullable=False, server_default="#e0e7ff"),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("meta_pixel_id", sa.String(100), nullable=True),
        sa.Column("redirect_url", sa.String(500), nullable=True),
        sa.Column("form_fields", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("views", sa.Integer, nullable=False, server_default="0"),
        sa.Column("conversions", sa.Integer, nullable=False, server_default="0"),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_landing_pages_plan_id", "landing_pages", ["plan_id"])

    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("landing_page_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("landing_pages.id"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=True),
        sa.Column("empresa", sa.String(200), nullable=True),
        sa.Column("telefono", sa.String(50), nullable=True),
        sa.Column("num_empleados", sa.String(50), nullable=True),
        sa.Column("extra_data", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("score", sa.Integer, nullable=True),
        sa.Column("segment", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_leads_user_id", "leads", ["user_id"])
    op.create_index("ix_leads_email", "leads", ["email"])


def downgrade() -> None:
    op.drop_table("leads")
    op.drop_table("landing_pages")
    op.drop_table("user_settings")
