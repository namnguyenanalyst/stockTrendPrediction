"""Allow undefined Sharpe and win rate without inventing numeric history values."""
from alembic import op
import sqlalchemy as sa

revision = "007_nullable_backtest_metrics"
down_revision = "006_user_management_audit"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("backtest_histories", sa.Column("config", sa.JSON(), nullable=False, server_default="{}"))
    for column in ("sharpe_ratio", "win_rate"):
        op.alter_column("backtest_histories", column, existing_type=sa.Float(), nullable=True)


def downgrade():
    op.drop_column("backtest_histories", "config")
    # Refuse loss of undefined-state information; operator must resolve rows explicitly.
    for column in ("sharpe_ratio", "win_rate"):
        op.alter_column("backtest_histories", column, existing_type=sa.Float(), nullable=False)
