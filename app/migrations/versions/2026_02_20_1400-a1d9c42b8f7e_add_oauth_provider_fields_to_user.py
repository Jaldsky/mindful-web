"""Add oauth_provider fields to User table

Revision ID: a1d9c42b8f7e
Revises: 5528e8091ddd
Create Date: 2026-02-20 14:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1d9c42b8f7e"
down_revision: Union[str, Sequence[str], None] = "5528e8091ddd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("oauth_provider", sa.String(length=50), nullable=True, comment="Внешний OAuth провайдер"),
    )
    op.add_column(
        "users",
        sa.Column(
            "oauth_provider_subject",
            sa.String(length=255),
            nullable=True,
            comment="Идентификатор пользователя у внешнего OAuth провайдера",
        ),
    )
    op.create_index(op.f("ix_users_oauth_provider"), "users", ["oauth_provider"], unique=False)
    op.create_index(op.f("ix_users_oauth_provider_subject"), "users", ["oauth_provider_subject"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_users_oauth_provider_subject"), table_name="users")
    op.drop_index(op.f("ix_users_oauth_provider"), table_name="users")
    op.drop_column("users", "oauth_provider_subject")
    op.drop_column("users", "oauth_provider")
