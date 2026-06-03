"""sale_content JSONB on landing_pages for sale subtype blocks

Revision ID: 0015_sale_content
Revises: 0014_sequence_events
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "0015_sale_content"
down_revision = "0014_sequence_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("landing_pages", sa.Column("sale_content", JSONB, nullable=True))


def downgrade() -> None:
    op.drop_column("landing_pages", "sale_content")
