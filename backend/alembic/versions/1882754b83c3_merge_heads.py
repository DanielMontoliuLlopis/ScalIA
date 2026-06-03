"""merge_heads

Revision ID: 1882754b83c3
Revises: 0019, 0019_recommendations
Create Date: 2026-05-26 21:49:12.771305

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1882754b83c3'
down_revision: Union[str, None] = ('0019', '0019_recommendations')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
