"""add creative_type and creatives to plans

Revision ID: 0013_creative_choice
Revises: 0012_stripe_subscription
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "0013_creative_choice"
down_revision = "0012_stripe_subscription"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("creative_type", sa.String(30), nullable=True))
    op.add_column("plans", sa.Column("creative_a", JSONB, nullable=True))
    op.add_column("plans", sa.Column("creative_b", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("plans", "creative_b")
    op.drop_column("plans", "creative_a")
    op.drop_column("plans", "creative_type")
