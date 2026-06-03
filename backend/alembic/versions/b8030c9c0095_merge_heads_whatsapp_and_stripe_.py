"""merge heads whatsapp and stripe subscription

Revision ID: b8030c9c0095
Revises: 0009_whatsapp, 0012_stripe_subscription
Create Date: 2026-05-25 12:43:21.860067

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b8030c9c0095'
down_revision: Union[str, None] = ('0009_whatsapp', '0012_stripe_subscription')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
