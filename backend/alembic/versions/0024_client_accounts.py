"""multi-cliente (workspaces) para tier agency

Revision ID: 0024_client_accounts
Revises: 0023_api_usage
Create Date: 2026-05-29
"""
from alembic import op
import sqlalchemy as sa


revision = "0024_client_accounts"
down_revision = "0023_api_usage"
branch_labels = None
depends_on = None


# Tablas de datos que pasan a estar scoped por client_account_id
DATA_TABLES = [
    "plans",
    "landing_pages",
    "leads",
    "lead_magnets",
    "recommendations",
    "sequence_events",
    "chat_sessions",
]


def upgrade() -> None:
    # ── 1. Tablas nuevas ──────────────────────────────────────────────
    op.create_table(
        "client_accounts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("logo_url", sa.String(500), nullable=True),
        sa.Column("business_type", sa.String(30), nullable=True),
        sa.Column("color_palette", sa.String(20), nullable=False, server_default="indigo"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_client_accounts_owner_id", "client_accounts", ["owner_id"])

    op.create_table(
        "client_account_members",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_account_id"], ["client_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("client_account_id", "user_id", name="uq_client_account_member"),
    )
    op.create_index("ix_cam_client", "client_account_members", ["client_account_id"])
    op.create_index("ix_cam_user", "client_account_members", ["user_id"])

    # ── 2. Columna client_account_id (nullable de momento) ────────────
    for table in DATA_TABLES:
        op.add_column(table, sa.Column("client_account_id", sa.UUID(), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_client_account",
            table,
            "client_accounts",
            ["client_account_id"],
            ["id"],
        )

    op.add_column("user_settings", sa.Column("client_account_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_user_settings_client_account",
        "user_settings",
        "client_accounts",
        ["client_account_id"],
        ["id"],
    )

    # ── 3. Backfill ───────────────────────────────────────────────────
    # 3.1 Un client_account por cada owner (parent_account_id IS NULL),
    #     usando datos de su user_settings si existen.
    op.execute(
        """
        INSERT INTO client_accounts (id, owner_id, name, logo_url, business_type, color_palette, created_at, updated_at)
        SELECT
            gen_random_uuid(),
            u.id,
            COALESCE(NULLIF(s.company_name, ''), u.full_name, u.email),
            s.logo_url,
            COALESCE(s.business_type, u.business_type),
            COALESCE(s.color_palette, 'indigo'),
            now(),
            now()
        FROM users u
        LEFT JOIN user_settings s ON s.user_id = u.id
        WHERE u.parent_account_id IS NULL
        """
    )

    # 3.2 Registrar a los sub-usuarios como miembros del client_account del owner.
    op.execute(
        """
        INSERT INTO client_account_members (id, client_account_id, user_id, role, created_at)
        SELECT gen_random_uuid(), ca.id, u.id, u.role, now()
        FROM users u
        JOIN client_accounts ca ON ca.owner_id = u.parent_account_id
        WHERE u.parent_account_id IS NOT NULL
        """
    )

    # 3.3 Backfill de cada tabla de datos. user_id apunta a un usuario;
    #     el client_account es el del owner (parent_account_id o el propio id).
    for table in DATA_TABLES:
        op.execute(
            f"""
            UPDATE {table} t
            SET client_account_id = ca.id
            FROM users u
            JOIN client_accounts ca ON ca.owner_id = COALESCE(u.parent_account_id, u.id)
            WHERE t.user_id = u.id
            """
        )

    # 3.4 Backfill de user_settings: solo el del owner es canónico.
    #     Los settings de sub-usuarios se eliminan (workspace comparte uno).
    op.execute(
        """
        UPDATE user_settings s
        SET client_account_id = ca.id
        FROM client_accounts ca
        WHERE ca.owner_id = s.user_id
        """
    )
    op.execute("DELETE FROM user_settings WHERE client_account_id IS NULL")

    # ── 4. user_settings: scope pasa a client_account_id ──────────────
    op.drop_constraint("user_settings_user_id_key", "user_settings", type_="unique")
    op.alter_column("user_settings", "user_id", existing_type=sa.UUID(), nullable=True)
    op.create_unique_constraint(
        "uq_user_settings_client_account", "user_settings", ["client_account_id"]
    )

    # ── 5. NOT NULL + índices ─────────────────────────────────────────
    op.alter_column("user_settings", "client_account_id", existing_type=sa.UUID(), nullable=False)
    op.create_index("ix_user_settings_ca", "user_settings", ["client_account_id"])

    for table in DATA_TABLES:
        op.alter_column(table, "client_account_id", existing_type=sa.UUID(), nullable=False)
        op.create_index(f"ix_{table}_ca", table, ["client_account_id"])


def downgrade() -> None:
    for table in DATA_TABLES:
        op.drop_index(f"ix_{table}_ca", table_name=table)
        op.drop_constraint(f"fk_{table}_client_account", table, type_="foreignkey")
        op.drop_column(table, "client_account_id")

    op.drop_index("ix_user_settings_ca", table_name="user_settings")
    op.drop_constraint("uq_user_settings_client_account", "user_settings", type_="unique")
    op.drop_constraint("fk_user_settings_client_account", "user_settings", type_="foreignkey")
    op.drop_column("user_settings", "client_account_id")
    op.create_unique_constraint("user_settings_user_id_key", "user_settings", ["user_id"])

    op.drop_index("ix_cam_user", table_name="client_account_members")
    op.drop_index("ix_cam_client", table_name="client_account_members")
    op.drop_table("client_account_members")
    op.drop_index("ix_client_accounts_owner_id", table_name="client_accounts")
    op.drop_table("client_accounts")
