"""add profile fields and subscription plan to users

Revision ID: 0011_user_profile_plan
Revises: 0010_funnel_choice_lead_magnets
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa


revision = "0011_user_profile_plan"
down_revision = "0010_funnel_choice_lead_magnets"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(200), nullable=True))
    op.add_column("users", sa.Column("phone", sa.String(50), nullable=True))
    op.add_column("users", sa.Column("business_type", sa.String(30), nullable=True))
    op.add_column(
        "users",
        sa.Column("plan", sa.String(20), nullable=False, server_default="trial"),
    )
    op.add_column(
        "users",
        sa.Column("active_campaigns_limit", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("users", "active_campaigns_limit")
    op.drop_column("users", "plan")
    op.drop_column("users", "business_type")
    op.drop_column("users", "phone")
    op.drop_column("users", "full_name")
