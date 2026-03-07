from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
import uuid

from app.db import Base


class ExecutionMetrics(Base):
    __tablename__ = "execution_metrics"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    org_id = Column(String)
    agent_id = Column(String)

    duplicate_blocks = Column(Integer, default=0)
    loop_blocks = Column(Integer, default=0)
    retry_blocks = Column(Integer, default=0)
    escalations = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
