"""Initial core schema: 5 tables (users, watchlists, presets, backtests, audits)

Revision ID: 001_initial_core_schema
Revises:
Create Date: 2026-10-30 17:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_core_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. users
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column(
            "role",
            sa.Enum("trader", "admin", name="user_role_enum", native_enum=False),
            nullable=False,
            server_default="trader",
        ),
        sa.Column(
            "risk_profile",
            sa.Enum(
                "conservative",
                "balanced",
                "aggressive",
                name="risk_profile_enum",
                native_enum=False,
            ),
            nullable=False,
            server_default="balanced",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    # 2. user_watchlists
    op.create_table(
        "user_watchlists",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column(
            "symbols",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        op.f("ix_user_watchlists_user_id"), "user_watchlists", ["user_id"], unique=False
    )

    # 3. strategy_presets
    op.create_table(
        "strategy_presets",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "parameters",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        op.f("ix_strategy_presets_user_id"), "strategy_presets", ["user_id"], unique=False
    )

    # 4. backtest_histories
    op.create_table(
        "backtest_histories",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", sa.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("strategy_name", sa.String(length=100), nullable=False),
        sa.Column("strategy_type", sa.String(length=50), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("initial_capital", sa.Float(), nullable=False),
        sa.Column("total_return", sa.Float(), nullable=False),
        sa.Column("sharpe_ratio", sa.Float(), nullable=False),
        sa.Column("max_drawdown", sa.Float(), nullable=False),
        sa.Column("win_rate", sa.Float(), nullable=False),
        sa.Column(
            "equity_curve",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "executed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index(
        op.f("ix_backtest_histories_user_id"), "backtest_histories", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_backtest_histories_symbol"), "backtest_histories", ["symbol"], unique=False
    )

    # 5. prediction_audits
    op.create_table(
        "prediction_audits",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("prediction_date", sa.Date(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("predicted_signal", sa.Integer(), nullable=False),
        sa.Column(
            "predicted_probabilities",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("actual_return", sa.Float(), nullable=True),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        op.f("ix_prediction_audits_symbol"), "prediction_audits", ["symbol"], unique=False
    )
    op.create_index(
        op.f("ix_prediction_audits_prediction_date"),
        "prediction_audits",
        ["prediction_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_prediction_audits_prediction_date"), table_name="prediction_audits")
    op.drop_index(op.f("ix_prediction_audits_symbol"), table_name="prediction_audits")
    op.drop_table("prediction_audits")

    op.drop_index(op.f("ix_backtest_histories_symbol"), table_name="backtest_histories")
    op.drop_index(op.f("ix_backtest_histories_user_id"), table_name="backtest_histories")
    op.drop_table("backtest_histories")

    op.drop_index(op.f("ix_strategy_presets_user_id"), table_name="strategy_presets")
    op.drop_table("strategy_presets")

    op.drop_index(op.f("ix_user_watchlists_user_id"), table_name="user_watchlists")
    op.drop_table("user_watchlists")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
