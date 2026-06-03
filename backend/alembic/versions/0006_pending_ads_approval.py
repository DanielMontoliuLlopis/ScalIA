"""pending_ads_approval status

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-22
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # PlanStatus is stored as String(50) — no schema change needed.
    # Migration exists to mark the revision chain.
    pass


def downgrade() -> None:
    pass
