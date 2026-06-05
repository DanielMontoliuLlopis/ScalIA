"""recommendations.applied_result — traza de ejecución Meta tras aprobación

Revision ID: 0030_recommendation_execution
Revises: 0029_metric_alerts
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "0030_recommendation_execution"
down_revision = "0029_metric_alerts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "recommendations",
        sa.Column("applied_result", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("recommendations", "applied_result")
