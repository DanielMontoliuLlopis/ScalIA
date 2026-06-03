"""add recommendations table

Revision ID: 0019_recommendations
Revises: 0018_lead_pipeline, 0018_offer_engine
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "0019_recommendations"
down_revision = ("0018_lead_pipeline", "0018_offer_engine")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "recommendations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("plan_id", UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("reasoning", sa.Text, nullable=False),
        sa.Column("action_payload", JSONB, nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_recommendations_plan_id", "recommendations", ["plan_id"])
    op.create_index("ix_recommendations_user_id", "recommendations", ["user_id"])
    op.create_index("ix_recommendations_status", "recommendations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_recommendations_status", "recommendations")
    op.drop_index("ix_recommendations_user_id", "recommendations")
    op.drop_index("ix_recommendations_plan_id", "recommendations")
    op.drop_table("recommendations")
