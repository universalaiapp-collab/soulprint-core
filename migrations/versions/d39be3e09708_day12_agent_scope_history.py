from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "day12_agent_scope_history"
down_revision = "e43f88c0b879"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_scope_history",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agents.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("scope", sa.JSON(), nullable=False),
        sa.Column("scope_version", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(),
                  server_default=sa.text("NOW()"),
                  nullable=False),
    )


def downgrade():
    op.drop_table("agent_scope_history")
