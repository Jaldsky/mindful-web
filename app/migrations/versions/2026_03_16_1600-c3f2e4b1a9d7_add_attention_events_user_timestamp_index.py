"""Add attention_events (user_id, timestamp) index

Revision ID: c3f2e4b1a9d7
Revises: a1d9c42b8f7e
Create Date: 2026-03-16 16:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c3f2e4b1a9d7"
down_revision: Union[str, Sequence[str], None] = "a1d9c42b8f7e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Idempotent creation: migration succeeds even if index already exists.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_attention_events_user_timestamp
        ON attention_events (user_id, timestamp);
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS idx_attention_events_user_timestamp;")
