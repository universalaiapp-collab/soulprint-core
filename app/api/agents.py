from fastapi import APIRouter, Depends, HTTPException, Request
from uuid import uuid4
from sqlalchemy import text
from datetime import datetime
import hashlib
import json

from app.db import SessionLocal
from app.core.crypto import generate_ed25519_keypair
from app.core.agent_validator import validate_agent
from app.core.agent_auth import verify_agent_request

router = APIRouter()


# ============================================================
# CREATE AGENT
# ============================================================

@router.post("/agents/create")
def create_agent(org_id: str, name: str):

    db = SessionLocal()

    keys = generate_ed25519_keypair()
    agent_id = str(uuid4())
    now = datetime.utcnow()

    db.execute(
        text("""
            INSERT INTO agents
            (id, org_id, name, public_key, scope_version, agent_status, created_at)
            VALUES (:id, :org_id, :name, :public_key, 1, 'active', :created)
        """),
        {
            "id": agent_id,
            "org_id": org_id,
            "name": name,
            "public_key": keys["public_key"],
            "created": now
        }
    )

    db.commit()
    db.close()

    return {
        "agent_id": agent_id,
        "public_key": keys["public_key"],
        "private_key": keys["private_key"]  # Returned ONCE
    }


# ============================================================
# SUSPEND AGENT
# ============================================================

@router.post("/agents/suspend")
def suspend_agent(agent_id: str):

    db = SessionLocal()

    db.execute(
        text("""
            UPDATE agents
            SET agent_status = 'suspended'
            WHERE id = :agent_id
        """),
        {"agent_id": agent_id}
    )

    db.commit()
    db.close()

    return {"status": "agent_suspended"}


# ============================================================
# REVOKE AGENT
# ============================================================

@router.post("/agents/revoke")
def revoke_agent(agent_id: str):

    db = SessionLocal()

    db.execute(
        text("""
            UPDATE agents
            SET agent_status = 'revoked'
            WHERE id = :agent_id
        """),
        {"agent_id": agent_id}
    )

    db.commit()
    db.close()

    return {"status": "agent_revoked"}


# ============================================================
# BASIC VALIDATION TEST
# ============================================================

@router.get("/agents/test-secure")
def test_secure(agent_id: str):

    validate_agent(agent_id)

    return {"message": "Agent authorized"}


# ============================================================
# SECURE ACTION (HASH CHAIN + IDEMPOTENCY)
# ============================================================

@router.post("/agents/secure-action")
async def secure_action(
    request: Request,
    agent_id: str = Depends(verify_agent_request)
):

    payload = await request.json()

    idempotency_key = request.headers.get("X-Idempotency-Key")

    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Missing Idempotency Key")

    request_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

    db = SessionLocal()

    # Check duplicate request
    existing = db.execute(
        text("""
            SELECT id FROM decision_ledger
            WHERE agent_id = :a
            AND idempotency_key = :k
        """),
        {"a": agent_id, "k": idempotency_key}
    ).fetchone()

    if existing:
        db.close()
        return {"message": "Duplicate request ignored"}

    # Get previous hash in chain
    last = db.execute(
        text("""
            SELECT response_hash
            FROM decision_ledger
            WHERE agent_id = :a
            ORDER BY created_at DESC
            LIMIT 1
        """),
        {"a": agent_id}
    ).fetchone()

    previous_hash = last[0] if last else ""

    # Simulated execution logic
    response = {"status": "executed"}

    response_hash = hashlib.sha256(
        json.dumps(response, sort_keys=True).encode()
    ).hexdigest()

    # Create chain hash
    chain_hash = hashlib.sha256(
        (previous_hash + request_hash + response_hash).encode()
    ).hexdigest()

    # Insert ledger entry
    db.execute(
        text("""
            INSERT INTO decision_ledger
            (agent_id, idempotency_key, request_hash, response_hash, previous_hash)
            VALUES (:a, :k, :rq, :rs, :ph)
        """),
        {
            "a": agent_id,
            "k": idempotency_key,
            "rq": request_hash,
            "rs": chain_hash,
            "ph": previous_hash
        }
    )

    # Update agent last_hash
    db.execute(
        text("""
            UPDATE agents
            SET last_hash = :h
            WHERE id = :a
        """),
        {"h": chain_hash, "a": agent_id}
    )

    db.commit()
    db.close()

    return {
        "result": response,
        "ledger_hash": chain_hash,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================
# UPDATE SCOPE (VERSIONING)
# ============================================================

@router.post("/agents/update-scope")
def update_scope(agent_id: str, scope: dict):

    db = SessionLocal()

    try:
        db.execute(text("BEGIN"))

        agent = db.execute(
            text("SELECT scope_version FROM agents WHERE id = :id FOR UPDATE"),
            {"id": agent_id}
        ).fetchone()

        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")

        new_version = agent[0] + 1

        db.execute(
            text("""
                UPDATE agents
                SET scope_version = :v
                WHERE id = :id
            """),
            {"v": new_version, "id": agent_id}
        )

        db.execute(
            text("""
                INSERT INTO agent_scope_history
                (agent_id, scope, scope_version)
                VALUES (:id, :scope, :v)
            """),
            {
                "id": agent_id,
                "scope": json.dumps(scope),
                "v": new_version
            }
        )

        db.commit()

        return {
            "agent_id": agent_id,
            "scope_version": new_version
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
