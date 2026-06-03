"""add whatsapp fields to user_settings

Revision ID: 0009_whatsapp
Revises: 0008_meta_page_id
Create Date: 2026-05-24
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_whatsapp"
down_revision: Union[str, None] = "0008_meta_page_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_settings", sa.Column("whatsapp_phone_number_id", sa.String(100), nullable=True))
    op.add_column("user_settings", sa.Column("whatsapp_phone_display", sa.String(30), nullable=True))


def downgrade() -> None:
    op.drop_column("user_settings", "whatsapp_phone_display")
    op.drop_column("user_settings", "whatsapp_phone_number_id")
