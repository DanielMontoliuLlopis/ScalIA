"""offer testing columns

Revision ID: 0019
Revises: 0018_offer_engine
Create Date: 2026-05-26
"""
from alembic import op
import sqlalchemy as sa

revision = "0019"
down_revision = "0018_offer_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plans", sa.Column("parent_plan_id", sa.UUID(), nullable=True))
    op.add_column("plans", sa.Column("is_offer_test", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("plans", sa.Column("offer_test_label", sa.String(100), nullable=True))
    op.create_foreign_key(
        "fk_plans_parent_plan_id", "plans", "plans",
        ["parent_plan_id"], ["id"], ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_plans_parent_plan_id", "plans", type_="foreignkey")
    op.drop_column("plans", "offer_test_label")
    op.drop_column("plans", "is_offer_test")
    op.drop_column("plans", "parent_plan_id")
