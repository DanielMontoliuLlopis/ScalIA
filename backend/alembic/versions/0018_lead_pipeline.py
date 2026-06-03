"""add lead pipeline fields: lead_status, closed_value, timestamps

Revision ID: 0018_lead_pipeline
Revises: 0017_company_profile
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa


revision = "0018_lead_pipeline"
down_revision = "0017_company_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("lead_status", sa.String(20), nullable=True, server_default="new"))
    op.add_column("leads", sa.Column("closed_value", sa.Numeric(12, 2), nullable=True))
    op.add_column("leads", sa.Column("meeting_scheduled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("leads", sa.Column("showed_up_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("leads", sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("leads", "closed_at")
    op.drop_column("leads", "showed_up_at")
    op.drop_column("leads", "meeting_scheduled_at")
    op.drop_column("leads", "closed_value")
    op.drop_column("leads", "lead_status")
