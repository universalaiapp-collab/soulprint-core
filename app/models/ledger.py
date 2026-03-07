from sqlalchemy import Column, String, DateTime
from datetime import datetime
from app.db import Base


class DecisionLedger(Base):
    __tablename__ = "decision_ledger"

    id = Column(String, primary_key=True)

    agent_id = Column(String)

    idempotency_key = Column(String)

    request_hash = Column(String)

    response_hash = Column(String)

    previous_hash = Column(String)

    decision_hash = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
