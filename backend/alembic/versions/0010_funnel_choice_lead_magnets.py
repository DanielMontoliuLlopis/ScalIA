"""add funnel_type/sale_type to plans and landings, create lead_magnets

Revision ID: 0010_funnel_choice_lead_magnets
Revises: 0009_plan_meta_campaign_id
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID


revision = "0010_funnel_choice_lead_magnets"
down_revision = "0009_plan_meta_campaign_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("funnel_type", sa.String(30), nullable=True))
    op.add_column("plans", sa.Column("sale_type", sa.String(20), nullable=True))
    op.add_column("plans", sa.Column("redirect_url", sa.String(500), nullable=True))

    op.add_column("landing_pages", sa.Column("funnel_type", sa.String(30), nullable=True))
    op.add_column("landing_pages", sa.Column("landing_subtype", sa.String(10), nullable=True))
    op.add_column("landing_pages", sa.Column("sale_type", sa.String(20), nullable=True))

    op.add_column("leads", sa.Column("scoring_breakdown", JSONB, nullable=True))

    op.create_table(
        "lead_magnets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("subtitle", sa.String(500), nullable=True),
        sa.Column("sections", JSONB, nullable=False, server_default="[]"),
        sa.Column("pdf_url", sa.Text(), nullable=True),
        sa.Column("pdf_html", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("lead_magnets")
    op.drop_column("leads", "scoring_breakdown")
    op.drop_column("landing_pages", "sale_type")
    op.drop_column("landing_pages", "landing_subtype")
    op.drop_column("landing_pages", "funnel_type")
    op.drop_column("plans", "redirect_url")
    op.drop_column("plans", "sale_type")
    op.drop_column("plans", "funnel_type")
