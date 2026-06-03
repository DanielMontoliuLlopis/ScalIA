"""merge heads whatsapp and stripe subscription

Revision ID: ff43928dd883
Revises: 0013_creative_choice
Create Date: 2026-05-25 17:24:24.320098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff43928dd883'
down_revision: Union[str, None] = ('0013_creative_choice', 'b8030c9c0095')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
