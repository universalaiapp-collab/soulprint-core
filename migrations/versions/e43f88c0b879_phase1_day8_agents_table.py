"""phase1_day8_agents_table

Revision ID: e43f88c0b879
Revises: 1fbe6ddea141
Create Date: 2026-02-25
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "e43f88c0b879"
down_revision = "1fbe6ddea141"
branch_labels = None
depends_on = None


def upgrade():
    # --------------------------------------------------
    # 1️⃣ Create ENUM safely (only if not exists)
    # --------------------------------------------------
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_type WHERE typname = 'agent_status_enum'
        ) THEN
            CREATE TYPE agent_status_enum AS ENUM (
                'active',
                'suspended',
                'revoked',
                'expired'
            );
        END IF;
    END
    $$;
    """)

    # --------------------------------------------------
    # 2️⃣ Create agents table
    # --------------------------------------------------
    op.create_table(
        "agents",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column(
            "scope_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
        sa.Column(
            "agent_status",
            postgresql.ENUM(
                "active",
                "suspended",
                "revoked",
                "expired",
                name="agent_status_enum",
                create_type=False,   # 🚨 Prevent duplicate creation
            ),
            nullable=False,
            server_default="active",
        ),
        sa.Column("expiry_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("last_hash", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
    )

    # --------------------------------------------------
    # 3️⃣ Create index
    # --------------------------------------------------
    op.create_index(
        "idx_agents_org_id",
        "agents",
        ["org_id"],
    )


def downgrade():
    # Drop index safely
    op.execute("DROP INDEX IF EXISTS idx_agents_org_id")

    # Drop table safely
    op.execute("DROP TABLE IF EXISTS agents")

    # Drop ENUM safely
    op.execute("DROP TYPE IF EXISTS agent_status_enum")
