"""Account management audit history."""
from alembic import op
import sqlalchemy as sa
revision = "006_user_management_audit"
down_revision = "005_account_flows"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("user_management_audits",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("actor", sa.String(255), nullable=True),
        sa.Column("target_id", sa.Uuid(), nullable=False),
        sa.Column("target_email", sa.String(255), nullable=False),
        sa.Column("old_role", sa.String(20), nullable=False),
        sa.Column("new_role", sa.String(20), nullable=False),
        sa.Column("old_active", sa.Boolean(), nullable=False),
        sa.Column("new_active", sa.Boolean(), nullable=False),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False))

def downgrade():
    op.drop_table("user_management_audits")
