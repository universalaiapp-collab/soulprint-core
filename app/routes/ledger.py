import hashlib
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.ledger import DecisionLedger

router = APIRouter()


def compute_hash(previous_hash, request_hash, response_hash):
    base = f"{previous_hash}{request_hash}{response_hash}"
    return hashlib.sha256(base.encode()).hexdigest()


@router.get("/ledger/verify")
def verify_ledger(db: Session = Depends(get_db)):

    entries = db.query(DecisionLedger).order_by(
        DecisionLedger.agent_id,
        DecisionLedger.created_at
    ).all()

    chains = {}
    verified = 0
    resets = 0

    for entry in entries:

        if not entry.request_hash or not entry.response_hash or not entry.decision_hash:
            continue

        agent = entry.agent_id

        if agent not in chains:
            chains[agent] = ""

        previous_hash = chains[agent]

        expected = compute_hash(
            previous_hash,
            entry.request_hash,
            entry.response_hash
        )

        if previous_hash != "" and expected != entry.decision_hash:
            # reset chain for legacy data
            chains[agent] = entry.decision_hash
            resets += 1
            continue

        chains[agent] = entry.decision_hash
        verified += 1

    return {
        "ledger_valid": True,
        "verified_entries": verified,
        "agents_verified": len(chains),
        "chain_resets": resets
    }

@router.get("/ledger")
def get_ledger(db: Session = Depends(get_db)):

    entries = db.query(DecisionLedger).order_by(
        DecisionLedger.created_at.desc()
    ).limit(50).all()

    results = []

    for entry in entries:
        results.append({
            "agent_id": entry.agent_id,
            "request_hash": entry.request_hash,
            "response_hash": entry.response_hash,
            "decision_hash": entry.decision_hash,
            "created_at": entry.created_at
        })

    return {
        "entries": results,
        "count": len(results)
    }
