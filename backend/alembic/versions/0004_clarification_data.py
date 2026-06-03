"""clarification_data in chat_messages

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-22
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("chat_messages",
        sa.Column("clarification_data", postgresql.JSONB, nullable=True)
    )


def downgrade() -> None:
    op.drop_column("chat_messages", "clarification_data")
