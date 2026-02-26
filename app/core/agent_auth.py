from fastapi import Request, HTTPException
from sqlalchemy import text
from app.db import SessionLocal
from app.core.crypto import verify_ed25519_signature


async def verify_agent_request(request: Request):

    agent_id = request.headers.get("X-Agent-Id")
    signature = request.headers.get("X-Agent-Signature")

    if not agent_id or not signature:
        raise HTTPException(status_code=401, detail="Missing agent authentication headers")

    db = SessionLocal()

    result = db.execute(
        text("""
            SELECT public_key
            FROM agents
            WHERE id = :agent_id
        """),
        {"agent_id": agent_id}
    ).fetchone()

    db.close()

    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")

    public_key = result[0]

    body = await request.body()

    valid = verify_ed25519_signature(
        public_key,
        body,
        signature
    )

    if not valid:
        raise HTTPException(status_code=403, detail="Invalid signature")

    return agent_id
