import json
import hashlib
import uuid
from datetime import datetime
from sqlalchemy import text

from app.services.escalation_engine import should_escalate


def canonical_fingerprint(payload: dict) -> str:
    """
    Canonical JSON hashing to ensure identical payloads
    produce the same fingerprint.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def secure_action_pipeline(org_id, agent_id, payload, db):

    fingerprint = canonical_fingerprint(payload)

    row = db.execute(
        text("""
        SELECT id,status,attempt_count,max_attempts
        FROM action_memory
        WHERE org_id=:org
        AND action_fingerprint=:fp
        """),
        {"org": org_id, "fp": fingerprint}
    ).fetchone()

    # --------------------------
    # FIREWALL CHECK
    # --------------------------

    if row:

        action_id, status, attempts, max_attempts = row

        if status == "complete":
            return {"status": "DENY_ALREADY_COMPLETE"}

        if attempts >= max_attempts:
            return {"status": "DENY_MAX_RETRY"}

        # retry update
        db.execute(
            text("""
            UPDATE action_memory
            SET attempt_count = attempt_count + 1,
                last_attempt_at = :now
            WHERE id=:id
            """),
            {"id": action_id, "now": datetime.utcnow()}
        )

        db.commit()

        return {"status": "DENY_LOOP"}

    # --------------------------
    # ESCALATION AUTO TRIGGER
    # --------------------------

    if should_escalate(payload):

        db.execute(
            text("""
            INSERT INTO escalation_queue
            (id,org_id,agent_id,action_type,payload,status,escalated_at)
            VALUES
            (:id,:org,:agent,:type,:payload,'pending',:now)
            """),
            {
                "id": str(uuid.uuid4()),
                "org": org_id,
                "agent": agent_id,
                "type": payload.get("action"),
                "payload": json.dumps(payload),
                "now": datetime.utcnow()
            }
        )

        db.commit()

        return {"status": "CHALLENGE_HUMAN"}

    # --------------------------
    # CREATE ACTION MEMORY
    # --------------------------

    action_id = str(uuid.uuid4())

    db.execute(
        text("""
        INSERT INTO action_memory
        (id,org_id,agent_id,action_fingerprint,status,
         attempt_count,max_attempts,first_attempt_at)
        VALUES
        (:id,:org,:agent,:fp,'running',1,3,:now)
        """),
        {
            "id": action_id,
            "org": org_id,
            "agent": agent_id,
            "fp": fingerprint,
            "now": datetime.utcnow()
        }
    )

    # --------------------------
    # LEDGER HASH CHAIN
    # --------------------------

    previous = db.execute(
        text("""
        SELECT last_hash
        FROM agents
        WHERE id=:agent
        """),
        {"agent": agent_id}
    ).fetchone()

    previous_hash = previous[0] if previous else None

    decision_hash = hashlib.sha256(
        f"{previous_hash}{agent_id}{payload}{datetime.utcnow()}".encode()
    ).hexdigest()

    db.execute(
        text("""
        INSERT INTO decision_ledger
        (id,org_id,agent_id,action_type,
         decision_hash,previous_hash,created_at)
        VALUES
        (:id,:org,:agent,:type,:hash,:prev,:now)
        """),
        {
            "id": str(uuid.uuid4()),
            "org": org_id,
            "agent": agent_id,
            "type": payload.get("action"),
            "hash": decision_hash,
            "prev": previous_hash,
            "now": datetime.utcnow()
        }
    )

    # update agent hash
    db.execute(
        text("""
        UPDATE agents
        SET last_hash=:hash
        WHERE id=:agent
        """),
        {"hash": decision_hash, "agent": agent_id}
    )

    # mark action complete
    db.execute(
        text("""
        UPDATE action_memory
        SET status='complete',
            result_hash=:hash,
            last_attempt_at=:now
        WHERE id=:id
        """),
        {
            "hash": decision_hash,
            "now": datetime.utcnow(),
            "id": action_id
        }
    )

    db.commit()

    return {
        "status": "EXECUTED",
        "decision_hash": decision_hash
    }
