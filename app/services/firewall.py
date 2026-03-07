from app.models.action_memory import ActionMemory
from app.services.fingerprint import canonical_fingerprint
from app.db import SessionLocal
from app.services.metrics_service import increment_metric

MAX_RETRY = 5


def check_firewall(org_id: str, agent_id: str, payload: dict) -> str:

    db = SessionLocal()

    try:

        fingerprint = canonical_fingerprint(payload)

        existing = db.query(ActionMemory).filter(
            ActionMemory.org_id == org_id,
            ActionMemory.agent_id == agent_id,
            ActionMemory.action_fingerprint == fingerprint
        ).first()

        # ------------------------------------------------
        # LOOP DETECTION
        # ------------------------------------------------
        if existing and existing.in_progress:
            increment_metric(org_id, "loops_blocked")
            return "DENY_LOOP"

        # ------------------------------------------------
        # MAX RETRY PROTECTION
        # ------------------------------------------------
        if existing and existing.retry_count >= MAX_RETRY:
            increment_metric(org_id, "retry_denied")
            return "DENY_MAX_RETRY"

        # ------------------------------------------------
        # DUPLICATE / ALREADY COMPLETED
        # ------------------------------------------------
        if existing and existing.completed:
            increment_metric(org_id, "duplicate_actions")
            return "DENY_ALREADY_COMPLETE"

        # ------------------------------------------------
        # UPDATE RETRY / CREATE MEMORY
        # ------------------------------------------------
        if existing:
            existing.retry_count += 1
            existing.in_progress = True

        else:
            new_entry = ActionMemory(
                org_id=org_id,
                agent_id=agent_id,
                action_fingerprint=fingerprint,
                retry_count=1,
                in_progress=True,
                completed=False
            )
            db.add(new_entry)

        db.commit()

        # ------------------------------------------------
        # ACTION ALLOWED
        # ------------------------------------------------
        increment_metric(org_id, "actions_executed")

        return "ALLOW"

    finally:
        db.close()
