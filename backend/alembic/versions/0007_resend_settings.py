"""resend api key and from email in user_settings

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-22
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_settings", sa.Column("resend_api_key", sa.Text(), nullable=True))
    op.add_column("user_settings", sa.Column("resend_from_email", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("user_settings", "resend_from_email")
    op.drop_column("user_settings", "resend_api_key")
