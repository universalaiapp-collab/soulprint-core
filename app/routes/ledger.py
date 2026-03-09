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
        DecisionLedger.created_at
    ).all()

    previous_hash = ""

    for entry in entries:

        expected_hash = compute_hash(
            previous_hash,
            entry.request_hash,
            entry.response_hash
        )

        if entry.decision_hash != expected_hash:
            return {
                "ledger_valid": False,
                "error": "ledger tampered"
            }

        previous_hash = entry.decision_hash

    return {
        "ledger_valid": True,
        "entries": len(entries)
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
