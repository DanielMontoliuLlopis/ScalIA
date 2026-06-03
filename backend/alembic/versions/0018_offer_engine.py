"""add offer engine fields to plans and template_id to landing_pages

Revision ID: 0018_offer_engine
Revises: 0017_company_profile
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa


revision = "0018_offer_engine"
down_revision = "0017_company_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("precio_base", sa.Numeric(10, 2), nullable=True))
    op.add_column("plans", sa.Column("tipo_oferta", sa.String(30), nullable=True))
    op.add_column("plans", sa.Column("urgencia", sa.String(50), nullable=True))
    op.add_column("plans", sa.Column("garantia", sa.String(50), nullable=True))
    op.add_column("plans", sa.Column("transformacion", sa.Text(), nullable=True))
    op.add_column("landing_pages", sa.Column("template_id", sa.String(30), nullable=True))


def downgrade() -> None:
    op.drop_column("plans", "precio_base")
    op.drop_column("plans", "tipo_oferta")
    op.drop_column("plans", "urgencia")
    op.drop_column("plans", "garantia")
    op.drop_column("plans", "transformacion")
    op.drop_column("landing_pages", "template_id")
