"""tabla metric_alerts — alertas automáticas sobre métricas

Revision ID: 0029_metric_alerts
Revises: 0028_metric_snapshots
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa


revision = "0029_metric_alerts"
down_revision = "0028_metric_snapshots"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "metric_alerts",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("client_account_id", sa.UUID(), nullable=False),
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("severity", sa.String(10), nullable=False, server_default="warning"),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("metric_key", sa.String(40), nullable=False, server_default=""),
        sa.Column("current_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("baseline_value", sa.Numeric(12, 4), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_account_id"], ["client_accounts.id"]),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"]),
        sa.UniqueConstraint("plan_id", "type", "snapshot_date", name="uq_metric_alert_identity"),
    )
    op.create_index("ix_metric_alerts_client_account_id", "metric_alerts", ["client_account_id"])
    op.create_index("ix_metric_alerts_plan_id", "metric_alerts", ["plan_id"])


def downgrade() -> None:
    op.drop_index("ix_metric_alerts_plan_id", table_name="metric_alerts")
    op.drop_index("ix_metric_alerts_client_account_id", table_name="metric_alerts")
    op.drop_table("metric_alerts")
