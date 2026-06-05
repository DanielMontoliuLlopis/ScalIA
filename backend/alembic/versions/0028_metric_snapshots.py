"""tabla metric_snapshots — snapshots diarios de Meta Insights (series + breakdowns)

Revision ID: 0028_metric_snapshots
Revises: 0027_lead_forms
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa


revision = "0028_metric_snapshots"
down_revision = "0027_lead_forms"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "metric_snapshots",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("meta_campaign_id", sa.String(100), nullable=False, server_default=""),
        sa.Column("meta_adset_id", sa.String(100), nullable=False, server_default=""),
        sa.Column("meta_ad_id", sa.String(100), nullable=False, server_default=""),
        sa.Column("level", sa.String(20), nullable=False),
        sa.Column("angle", sa.String(40), nullable=True),
        sa.Column("breakdown_key", sa.String(40), nullable=False, server_default=""),
        sa.Column("breakdown_value", sa.String(120), nullable=False, server_default=""),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reach", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conversions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spend", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Numeric(12, 2), nullable=False, server_default="0"),
        sa.Column("ctr", sa.Numeric(8, 4), nullable=True),
        sa.Column("cpc", sa.Numeric(10, 4), nullable=True),
        sa.Column("cpm", sa.Numeric(10, 4), nullable=True),
        sa.Column("cpl", sa.Numeric(10, 2), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_account_id"], ["client_accounts.id"]),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"]),
        sa.UniqueConstraint(
            "plan_id",
            "level",
            "meta_adset_id",
            "meta_ad_id",
            "breakdown_key",
            "breakdown_value",
            "snapshot_date",
            name="uq_metric_snapshot_identity",
        ),
    )
    op.create_index("ix_metric_snapshots_client_account_id", "metric_snapshots", ["client_account_id"])
    op.create_index("ix_metric_snapshots_plan_id", "metric_snapshots", ["plan_id"])
    op.create_index("ix_metric_snapshots_snapshot_date", "metric_snapshots", ["snapshot_date"])
    op.create_index("ix_metric_snapshots_angle", "metric_snapshots", ["angle"])


def downgrade() -> None:
    op.drop_index("ix_metric_snapshots_angle", table_name="metric_snapshots")
    op.drop_index("ix_metric_snapshots_snapshot_date", table_name="metric_snapshots")
    op.drop_index("ix_metric_snapshots_plan_id", table_name="metric_snapshots")
    op.drop_index("ix_metric_snapshots_client_account_id", table_name="metric_snapshots")
    op.drop_table("metric_snapshots")
