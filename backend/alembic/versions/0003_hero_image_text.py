"""hero_image_url as Text

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-22
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("landing_pages", "hero_image_url",
                    existing_type=sa.String(500),
                    type_=sa.Text(),
                    existing_nullable=True)


def downgrade() -> None:
    op.alter_column("landing_pages", "hero_image_url",
                    existing_type=sa.Text(),
                    type_=sa.String(500),
                    existing_nullable=True)
