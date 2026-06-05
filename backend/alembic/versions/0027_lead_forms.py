"""tabla lead_forms + plans.lead_form_id + user_settings.privacy_policy_url

Revision ID: 0027_lead_forms
Revises: 0026_angle_performance
Create Date: 2026-06-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0027_lead_forms"
down_revision = "0026_angle_performance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lead_forms",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("locale", sa.String(10), nullable=False, server_default="es_ES"),
        sa.Column("intro_headline", sa.String(300), nullable=True),
        sa.Column("intro_description", sa.Text(), nullable=True),
        sa.Column("fields", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("privacy_policy_url", sa.String(500), nullable=True),
        sa.Column("privacy_policy_link_text", sa.String(200), nullable=True),
        sa.Column("thank_you_title", sa.String(300), nullable=True),
        sa.Column("thank_you_body", sa.Text(), nullable=True),
        sa.Column("thank_you_button_text", sa.String(100), nullable=True),
        sa.Column("thank_you_button_type", sa.String(30), nullable=False, server_default="VIEW_WEBSITE"),
        sa.Column("thank_you_website_url", sa.String(500), nullable=True),
        sa.Column("meta_form_id", sa.String(100), nullable=True),
        sa.Column("meta_page_id", sa.String(100), nullable=True),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_account_id"], ["client_accounts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_lead_forms_client_account_id", "lead_forms", ["client_account_id"])

    op.add_column("plans", sa.Column("lead_form_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "fk_plans_lead_form_id", "plans", "lead_forms", ["lead_form_id"], ["id"]
    )

    op.add_column("user_settings", sa.Column("privacy_policy_url", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("user_settings", "privacy_policy_url")
    op.drop_constraint("fk_plans_lead_form_id", "plans", type_="foreignkey")
    op.drop_column("plans", "lead_form_id")
    op.drop_index("ix_lead_forms_client_account_id", table_name="lead_forms")
    op.drop_table("lead_forms")
