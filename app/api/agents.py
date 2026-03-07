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

from app.services.firewall import check_firewall
from app.services.escalation_engine import should_escalate
from app.services.fingerprint import canonical_fingerprint
from app.models.action_memory import ActionMemory
from app.core.rate_limit import check_org_rate_limit
from sqlalchemy import text

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
        "private_key": keys["private_key"]
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
# SECURE ACTION (FIREWALL + HASH CHAIN)
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

    db = SessionLocal()

    # --------------------------------------------------------
    # Resolve org_id
    # --------------------------------------------------------
    org_row = db.execute(
        text("SELECT org_id FROM agents WHERE id = :a"),
        {"a": agent_id}
    ).fetchone()

    if not org_row:
        db.close()
        raise HTTPException(status_code=404, detail="Agent not found")

    org_id = org_row[0]

    # --------------------------------------------------------
    # RATE LIMIT PER ORG  ✅ FIXED LOCATION
    # --------------------------------------------------------
    org = db.execute(
        text("SELECT rate_limit_per_sec FROM organizations WHERE id=:id"),
        {"id": org_id}
    ).fetchone()

    limit = org[0] if org else 5

    if not check_org_rate_limit(org_id, limit):
        db.close()
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    # --------------------------------------------------------
    # FIREWALL CHECK
    # --------------------------------------------------------
    decision = check_firewall(org_id, agent_id, payload)

    if decision != "ALLOW":
        db.close()
        return {"status": decision}

    # --------------------------------------------------------
    # ESCALATION CHECK
    # --------------------------------------------------------
    if should_escalate(payload):

        fingerprint = canonical_fingerprint(payload)

        db.execute(
            text("""
                INSERT INTO escalation_queue
                (org_id, agent_id, payload, action_fingerprint, status, created_at)
                VALUES (:o, :a, :p, :f, 'pending', :c)
            """),
            {
                "o": org_id,
                "a": agent_id,
                "p": json.dumps(payload),
                "f": fingerprint,
                "c": datetime.utcnow()
            }
        )

        db.commit()
        db.close()

        return {"status": "CHALLENGE_HUMAN"}

    # --------------------------------------------------------
    # IDEMPOTENCY CHECK (Ledger Level)
    # --------------------------------------------------------
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

    # --------------------------------------------------------
    # HASH CHAIN
    # --------------------------------------------------------
    request_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode()
    ).hexdigest()

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

    response = {"status": "executed"}

    response_hash = hashlib.sha256(
        json.dumps(response, sort_keys=True).encode()
    ).hexdigest()

    decision_hash = hashlib.sha256(
    (previous_hash + request_hash + response_hash).encode()
     ).hexdigest()

    db.execute(
    text("""
        INSERT INTO decision_ledger
        (agent_id, idempotency_key, request_hash, response_hash, previous_hash, decision_hash)
        VALUES (:a, :k, :rq, :rs, :ph, :dh)
    """),
    {
        "a": agent_id,
        "k": idempotency_key,
        "rq": request_hash,
        "rs": response_hash,
        "ph": previous_hash,
        "dh": decision_hash
    }
    )

    db.execute(
    text("""
        UPDATE agents
        SET last_hash = :h
        WHERE id = :a
    """),
    {"h": decision_hash, "a": agent_id}
    )

    # --------------------------------------------------------
    # UPDATE FIREWALL MEMORY
    # --------------------------------------------------------
    fingerprint = canonical_fingerprint(payload)

    memory = db.query(ActionMemory).filter(
        ActionMemory.org_id == org_id,
        ActionMemory.agent_id == agent_id,
        ActionMemory.action_fingerprint == fingerprint
    ).first()

    if memory:
        memory.completed = True
        memory.in_progress = False

    db.commit()
    db.close()

    return {
    "result": response,
    "ledger_hash": decision_hash,
    "timestamp": datetime.utcnow().isoformat()
    }
