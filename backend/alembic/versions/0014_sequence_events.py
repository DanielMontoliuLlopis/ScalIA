"""sequence_events table for per-lead nurturing tracking

Revision ID: 0014_sequence_events
Revises: 0013_creative_choice
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "0014_sequence_events"
down_revision = "0013_creative_choice"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy.dialects.postgresql import JSONB
    op.add_column("leads", sa.Column("recommended_action", JSONB, nullable=True))
    op.add_column("leads", sa.Column("action_completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("leads", sa.Column("action_note", sa.String(500), nullable=True))

    op.create_table(
        "sequence_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", UUID(as_uuid=True), sa.ForeignKey("leads.id"), nullable=False),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False),
        sa.Column("order", sa.Integer, nullable=False),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("preview", sa.Text, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="scheduled"),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_sequence_events_lead", "sequence_events", ["lead_id"])
    op.create_index("ix_sequence_events_plan", "sequence_events", ["plan_id"])


def downgrade() -> None:
    op.drop_index("ix_sequence_events_plan", table_name="sequence_events")
    op.drop_index("ix_sequence_events_lead", table_name="sequence_events")
    op.drop_table("sequence_events")
    op.drop_column("leads", "action_note")
    op.drop_column("leads", "action_completed_at")
    op.drop_column("leads", "recommended_action")
