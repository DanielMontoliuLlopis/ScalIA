"""add business_description and business_type to user_settings

Revision ID: 0017_company_profile
Revises: 0016_ab_testing
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa


revision = "0017_company_profile"
down_revision = "0016_ab_testing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("business_description", sa.Text(), nullable=True),
    )
    op.add_column(
        "user_settings",
        sa.Column("business_type", sa.String(20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "business_type")
    op.drop_column("user_settings", "business_description")
