"""tabla angle_performance — histórico ángulo × business_type × resultado

Revision ID: 0026_angle_performance
Revises: 0025_multi_angle_research
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa


revision = "0026_angle_performance"
down_revision = "0025_multi_angle_research"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "angle_performance",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=True),
        sa.Column("plan_id", sa.UUID(), nullable=False),
        sa.Column("business_type", sa.String(30), nullable=False),
        sa.Column("angle", sa.String(40), nullable=False),
        sa.Column("tipo_oferta", sa.String(30), nullable=True),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("leads", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("spend", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("ctr", sa.Numeric(6, 4), nullable=True),
        sa.Column("cpl", sa.Numeric(10, 2), nullable=True),
        sa.Column("roas", sa.Numeric(8, 2), nullable=True),
        sa.Column("result", sa.String(20), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["plan_id"], ["plans.id"]),
    )
    op.create_index("ix_angle_perf_user", "angle_performance", ["user_id"])
    op.create_index("ix_angle_perf_account", "angle_performance", ["account_id"])
    op.create_index("ix_angle_perf_business_type", "angle_performance", ["business_type"])
    op.create_index("ix_angle_perf_angle", "angle_performance", ["angle"])


def downgrade() -> None:
    op.drop_index("ix_angle_perf_angle", table_name="angle_performance")
    op.drop_index("ix_angle_perf_business_type", table_name="angle_performance")
    op.drop_index("ix_angle_perf_account", table_name="angle_performance")
    op.drop_index("ix_angle_perf_user", table_name="angle_performance")
    op.drop_table("angle_performance")
