"""roles de equipo, programa fundadores y migración a 3 tiers

Revision ID: 0020_roles_founder
Revises: 1882754b83c3
Create Date: 2026-05-28
"""
from alembic import op
import sqlalchemy as sa


revision = "0020_roles_founder"
down_revision = "1882754b83c3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(20), nullable=False, server_default="owner"),
    )
    op.add_column(
        "users",
        sa.Column("parent_account_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("is_founder", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_users_parent_account_id", "users", ["parent_account_id"])
    op.create_foreign_key(
        "fk_users_parent_account_id",
        "users",
        "users",
        ["parent_account_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # Migrar tiers antiguos -> nuevos
    op.execute("UPDATE users SET plan = 'growth' WHERE plan = 'pro'")
    op.execute("UPDATE users SET plan = 'agency' WHERE plan = 'business'")
    # Ajustar límites de campañas al nuevo esquema
    op.execute("UPDATE users SET active_campaigns_limit = 3 WHERE plan = 'growth'")
    op.execute("UPDATE users SET active_campaigns_limit = 9999 WHERE plan = 'agency'")
    op.execute("UPDATE users SET active_campaigns_limit = 1 WHERE plan = 'starter'")


def downgrade() -> None:
    op.execute("UPDATE users SET plan = 'pro' WHERE plan IN ('starter', 'growth')")
    op.execute("UPDATE users SET plan = 'business' WHERE plan = 'agency'")
    op.drop_constraint("fk_users_parent_account_id", "users", type_="foreignkey")
    op.drop_index("ix_users_parent_account_id", table_name="users")
    op.drop_column("users", "is_founder")
    op.drop_column("users", "parent_account_id")
    op.drop_column("users", "role")
