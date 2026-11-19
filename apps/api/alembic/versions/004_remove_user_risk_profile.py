"""Remove unused risk profile. Downgrade cannot recover original choices."""
from alembic import op
import sqlalchemy as sa

revision = "004_remove_user_risk_profile"
down_revision = "003_refresh_sessions"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column("users", "risk_profile")


def downgrade():
    op.add_column("users", sa.Column(
        "risk_profile",
        sa.Enum("conservative", "balanced", "aggressive",
                name="risk_profile_enum", native_enum=False),
        nullable=False, server_default="balanced",
    ))
