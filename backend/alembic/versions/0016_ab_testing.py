"""add ab_testing column to plans

Revision ID: 0016_ab_testing
Revises: 0015_sale_content
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa


revision = "0016_ab_testing"
down_revision = ("0015_sale_content", "ff43928dd883")
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "plans",
        sa.Column("ab_testing", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("plans", "ab_testing")
