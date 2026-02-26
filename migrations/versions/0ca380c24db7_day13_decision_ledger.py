from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "day13_decision_ledger"
down_revision = "day12_agent_scope_history"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "decision_ledger",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("agents.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("idempotency_key", sa.Text(), nullable=False),
        sa.Column("request_hash", sa.Text(), nullable=False),
        sa.Column("response_hash", sa.Text(), nullable=False),
        sa.Column("previous_hash", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(),
                  server_default=sa.text("NOW()"),
                  nullable=False),
        sa.UniqueConstraint("agent_id", "idempotency_key",
                            name="uq_agent_idempotency")
    )


def downgrade():
    op.drop_table("decision_ledger")
