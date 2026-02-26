from sqlalchemy import Column, Text, Integer, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.sql import func
from app.db.base import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    name = Column(Text, nullable=False)
    public_key = Column(Text, nullable=False)

    scope_version = Column(Integer, default=1)

    agent_status = Column(
        ENUM(
            "active",
            "suspended",
            "revoked",
            "expired",
            name="agent_status_enum",
            create_type=False,
        ),
        default="active",
        nullable=False,
    )

    expiry_at = Column(TIMESTAMP, nullable=True)
    last_hash = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
