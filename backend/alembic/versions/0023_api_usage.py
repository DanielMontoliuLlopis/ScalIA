"""rastreo de uso OpenAI: tokens y costes

Revision ID: 0023_api_usage
Revises: 0022_closer_auth
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa


revision = "0023_api_usage"
down_revision = "0022_closer_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_usage",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=True),
        sa.Column("model", sa.String(50), nullable=False, server_default="gpt-4o"),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_usd", sa.Numeric(10, 6), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_api_usage_user_id", "api_usage", ["user_id"])
    op.create_index("ix_api_usage_plan_id", "api_usage", ["plan_id"])
    op.create_index("ix_api_usage_agent_name", "api_usage", ["agent_name"])
    op.create_index("ix_api_usage_created_at", "api_usage", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_api_usage_created_at", table_name="api_usage")
    op.drop_index("ix_api_usage_agent_name", table_name="api_usage")
    op.drop_index("ix_api_usage_plan_id", table_name="api_usage")
    op.drop_index("ix_api_usage_user_id", table_name="api_usage")
    op.drop_table("api_usage")
