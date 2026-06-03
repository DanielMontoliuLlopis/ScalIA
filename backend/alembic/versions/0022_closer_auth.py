"""login de closers: password para acceso al portal

Revision ID: 0022_closer_auth
Revises: 0021_admin_closers
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa


revision = "0022_closer_auth"
down_revision = "0021_admin_closers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("closers", sa.Column("hashed_password", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("closers", "hashed_password")
