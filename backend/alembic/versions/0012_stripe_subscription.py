"""add stripe customer and subscription fields to users

Revision ID: 0012_stripe_subscription
Revises: 0011_user_profile_plan
Create Date: 2026-05-25
"""
from alembic import op
import sqlalchemy as sa


revision = "0012_stripe_subscription"
down_revision = "0011_user_profile_plan"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("stripe_customer_id", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("stripe_subscription_id", sa.String(100), nullable=True))
    op.add_column("users", sa.Column("subscription_status", sa.String(30), nullable=True))
    op.add_column(
        "users",
        sa.Column("subscription_current_period_end", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_users_stripe_customer_id", "users", ["stripe_customer_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_users_stripe_customer_id", table_name="users")
    op.drop_column("users", "subscription_current_period_end")
    op.drop_column("users", "subscription_status")
    op.drop_column("users", "stripe_subscription_id")
    op.drop_column("users", "stripe_customer_id")
