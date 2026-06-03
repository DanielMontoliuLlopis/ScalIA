"""add meta_page_id to user_settings

Revision ID: 0008_meta_page_id
Revises: 0007_resend_settings
Create Date: 2026-05-24
"""
from alembic import op
import sqlalchemy as sa

revision = "0008_meta_page_id"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("meta_page_id", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "meta_page_id")
