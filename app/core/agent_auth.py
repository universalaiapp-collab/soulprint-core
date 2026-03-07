from fastapi import Request, HTTPException
from sqlalchemy import text
from app.db import SessionLocal
from app.core.crypto import verify_ed25519_signature
from datetime import datetime, timezone
import json


MAX_REQUEST_AGE_SECONDS = 60


async def verify_agent_request(request: Request):

    # ------------------------------------------------
    # Read headers (case insensitive)
    # ------------------------------------------------
    headers = request.headers

    agent_id = (
        headers.get("X-Agent-Id")
        or headers.get("x-agent-id")
        or headers.get("X-Agent-ID")
    )

    signature = (
        headers.get("X-Agent-Signature")
        or headers.get("x-agent-signature")
        or headers.get("X-Agent-SIGNATURE")
    )

    timestamp = (
        headers.get("X-Timestamp")
        or headers.get("x-timestamp")
        or headers.get("X-TIMESTAMP")
    )

    if not agent_id or not signature or not timestamp:
        raise HTTPException(
            status_code=401,
            detail="Missing agent authentication headers"
        )

    # ------------------------------------------------
    # Replay protection (timestamp validation)
    # ------------------------------------------------
    try:
        request_time = datetime.fromisoformat(timestamp)

        if request_time.tzinfo is None:
            request_time = request_time.replace(tzinfo=timezone.utc)

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid timestamp format"
        )

    now = datetime.now(timezone.utc)

    age = abs((now - request_time).total_seconds())

    if age > MAX_REQUEST_AGE_SECONDS:
        raise HTTPException(
            status_code=401,
            detail="Request expired"
        )

    # ------------------------------------------------
    # Load agent public key
    # ------------------------------------------------
    db = SessionLocal()

    try:

        result = db.execute(
            text("""
                SELECT public_key
                FROM agents
                WHERE id = :agent_id
            """),
            {"agent_id": agent_id}
        ).fetchone()

    finally:
        db.close()

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Agent not found"
        )

    public_key = result[0]

    # ------------------------------------------------
    # Canonicalize request body for signature verification
    # ------------------------------------------------
    body = await request.body()

    try:
        parsed = json.loads(body)

        canonical = json.dumps(
            parsed,
            separators=(",", ":"),
            sort_keys=True
        ).encode()

    except Exception:
        canonical = body

    # ------------------------------------------------
    # Verify ed25519 signature
    # ------------------------------------------------
    valid = verify_ed25519_signature(
        public_key,
        canonical,
        signature
    )

    if not valid:
        raise HTTPException(
            status_code=403,
            detail="Invalid signature"
        )

    return agent_id
