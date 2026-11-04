"""Add last_seen_at to users table

Revision ID: 002_add_last_seen_at_to_users
Revises: 001_initial_core_schema
Create Date: 2026-11-04 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_add_last_seen_at_to_users"
down_revision: str | None = "001_initial_core_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(op.f("ix_users_last_seen_at"), "users", ["last_seen_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_last_seen_at"), table_name="users")
    op.drop_column("users", "last_seen_at")
