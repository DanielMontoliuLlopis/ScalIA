"""add meta_campaign_id to plans

Revision ID: 0009_plan_meta_campaign_id
Revises: 0008_meta_page_id
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa

revision = "0009_plan_meta_campaign_id"
down_revision = "0008_meta_page_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("meta_campaign_id", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("plans", "meta_campaign_id")
