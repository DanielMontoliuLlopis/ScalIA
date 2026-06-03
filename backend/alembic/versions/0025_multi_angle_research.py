"""multi-angle testing + research export mode + scans

Revision ID: 0025_multi_angle_research
Revises: 0024_client_accounts
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "0025_multi_angle_research"
down_revision = "0024_client_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── plans: Multi-Angle Testing + Research Export ──────────────────
    op.add_column("plans", sa.Column("ab_mode", sa.String(20), nullable=False, server_default="ab_classic"))
    op.add_column("plans", sa.Column("num_angles", sa.Integer(), nullable=True))
    op.add_column("plans", sa.Column("angles_tested", JSONB(), nullable=True))
    op.add_column("plans", sa.Column("research_export", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("plans", sa.Column("export_url", sa.String(500), nullable=True))

    # ── users: saldo de escaneos Research Mode ────────────────────────
    op.add_column("users", sa.Column("scans_remaining", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("scans_reset_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "scans_reset_at")
    op.drop_column("users", "scans_remaining")
    op.drop_column("plans", "export_url")
    op.drop_column("plans", "research_export")
    op.drop_column("plans", "angles_tested")
    op.drop_column("plans", "num_angles")
    op.drop_column("plans", "ab_mode")
