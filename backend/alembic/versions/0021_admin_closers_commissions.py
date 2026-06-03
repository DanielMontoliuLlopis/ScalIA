"""panel admin: superadmin, closers y comisiones

Revision ID: 0021_admin_closers
Revises: 0020_roles_founder
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa


revision = "0021_admin_closers"
down_revision = "0020_roles_founder"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users: flag superadmin + atribución a closer ──────────────────────────
    op.add_column(
        "users",
        sa.Column("is_superadmin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "users",
        sa.Column("closer_id", sa.UUID(), nullable=True),
    )

    # ── closers ───────────────────────────────────────────────────────────────
    op.create_table(
        "closers",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column(
            "commission_rate",
            sa.Numeric(5, 4),
            nullable=False,
            server_default="0.0600",
        ),
        sa.Column("referral_code", sa.String(40), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_closers_referral_code", "closers", ["referral_code"], unique=True)

    # FK users.closer_id -> closers.id (después de crear la tabla)
    op.create_index("ix_users_closer_id", "users", ["closer_id"])
    op.create_foreign_key(
        "fk_users_closer_id",
        "users",
        "closers",
        ["closer_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ── commissions ─────────────────────────────────────────────────────────────
    op.create_table(
        "commissions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("closer_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("stripe_invoice_id", sa.String(100), nullable=False, unique=True),
        # tipo: first_quota | recurring
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("base_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("commission_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="eur"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
        # estado: pending | paid
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["closer_id"], ["closers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_commissions_closer_id", "commissions", ["closer_id"])
    op.create_index("ix_commissions_user_id", "commissions", ["user_id"])
    op.create_index(
        "ix_commissions_stripe_invoice_id", "commissions", ["stripe_invoice_id"], unique=True
    )

    # Marcar superadmin a los owners por email
    op.execute(
        "UPDATE users SET is_superadmin = true "
        "WHERE lower(email) = 'llodamont@gmail.com'"
    )


def downgrade() -> None:
    op.drop_index("ix_commissions_stripe_invoice_id", table_name="commissions")
    op.drop_index("ix_commissions_user_id", table_name="commissions")
    op.drop_index("ix_commissions_closer_id", table_name="commissions")
    op.drop_table("commissions")

    op.drop_constraint("fk_users_closer_id", "users", type_="foreignkey")
    op.drop_index("ix_users_closer_id", table_name="users")

    op.drop_index("ix_closers_referral_code", table_name="closers")
    op.drop_table("closers")

    op.drop_column("users", "closer_id")
    op.drop_column("users", "is_superadmin")
