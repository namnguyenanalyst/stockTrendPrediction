"""Persist refresh sessions without storing bearer credentials.

Revision ID: 003_refresh_sessions
Revises: 002_add_last_seen_at_to_users
"""

from alembic import op
import sqlalchemy as sa

revision = "003_refresh_sessions"
down_revision = "002_add_last_seen_at_to_users"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("refresh_sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_refresh_sessions_user_id", "refresh_sessions", ["user_id"])


def downgrade():
    op.drop_index("ix_refresh_sessions_user_id", table_name="refresh_sessions")
    op.drop_table("refresh_sessions")
