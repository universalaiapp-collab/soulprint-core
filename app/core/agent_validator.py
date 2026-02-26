from sqlalchemy import text
from datetime import datetime
from fastapi import HTTPException
from app.db import SessionLocal


def validate_agent(agent_id: str):

    db = SessionLocal()

    result = db.execute(
        text("""
            SELECT agent_status, expiry_at
            FROM agents
            WHERE id = :agent_id
        """),
        {"agent_id": agent_id}
    ).fetchone()

    db.close()

    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")

    status, expiry_at = result

    if status == "revoked":
        raise HTTPException(status_code=403, detail="Agent revoked")

    if status == "suspended":
        raise HTTPException(status_code=403, detail="Agent suspended")

    if expiry_at and expiry_at < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Agent expired")

    return True
