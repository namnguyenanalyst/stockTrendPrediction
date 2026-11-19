"""Account verification, recovery and persistent limits."""

import sqlalchemy as sa
from alembic import op

revision = "005_account_flows"
down_revision = "004_remove_user_risk_profile"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "users", sa.Column("auth_version", sa.Integer(), server_default="0", nullable=False)
    )
    op.create_table(
        "account_actions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column(
            "user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("purpose", sa.String(20), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_account_actions_user_id", "account_actions", ["user_id"])
    op.create_table(
        "account_rate_limits",
        sa.Column("key", sa.String(64), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade():
    op.drop_table("account_rate_limits")
    op.drop_index("ix_account_actions_user_id", table_name="account_actions")
    op.drop_table("account_actions")
    op.drop_column("users", "auth_version")
    op.drop_column("users", "email_verified_at")
