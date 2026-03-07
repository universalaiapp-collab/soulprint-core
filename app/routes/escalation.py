from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from app.db import SessionLocal
from app.services.escalation_executor import execute_approved

router = APIRouter()


# -------------------------------
# APPROVE ESCALATION
# -------------------------------
@router.post("/escalation/approve")
def approve(escalation_id: str):

    db = SessionLocal()

    row = db.execute(
        text("SELECT id, status FROM escalation_queue WHERE id = :id"),
        {"id": escalation_id}
    ).fetchone()

    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="Escalation not found")

    if row[1] != "pending":
        db.close()
        raise HTTPException(status_code=400, detail="Escalation already processed")

    db.execute(
        text("""
            UPDATE escalation_queue
            SET status = 'approved'
            WHERE id = :id
        """),
        {"id": escalation_id}
    )

    db.commit()
    db.close()

    return {"status": "approved"}


# -------------------------------
# DENY ESCALATION
# -------------------------------
@router.post("/escalation/deny")
def deny(escalation_id: str):

    db = SessionLocal()

    row = db.execute(
        text("SELECT id FROM escalation_queue WHERE id = :id"),
        {"id": escalation_id}
    ).fetchone()

    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="Escalation not found")

    db.execute(
        text("""
            UPDATE escalation_queue
            SET status = 'denied'
            WHERE id = :id
        """),
        {"id": escalation_id}
    )

    db.commit()
    db.close()

    return {"status": "denied"}


# -------------------------------
# LIST PENDING ESCALATIONS
# -------------------------------
@router.get("/escalation/pending")
def list_pending():

    db = SessionLocal()

    rows = db.execute(
        text("""
            SELECT id, agent_id, payload, created_at
            FROM escalation_queue
            WHERE status = 'pending'
            ORDER BY created_at DESC
        """)
    ).fetchall()

    db.close()

    return [
        {
            "id": r[0],
            "agent_id": r[1],
            "payload": r[2],
            "created_at": r[3]
        }
        for r in rows
    ]


# -------------------------------
# EXECUTE APPROVED ESCALATION
# -------------------------------
@router.post("/escalation/execute")
def execute(escalation_id: str):

    db = SessionLocal()

    row = db.execute(
        text("""
            SELECT id, status
            FROM escalation_queue
            WHERE id = :id
        """),
        {"id": escalation_id}
    ).fetchone()

    if not row:
        db.close()
        raise HTTPException(status_code=404, detail="Escalation not found")

    if row[1] != "approved":
        db.close()
        raise HTTPException(
            status_code=400,
            detail="Escalation must be approved before execution"
        )

    # Execute the original action
    result = execute_approved(escalation_id, db)

    db.execute(
        text("""
            UPDATE escalation_queue
            SET status = 'executed'
            WHERE id = :id
        """),
        {"id": escalation_id}
    )

    db.commit()
    db.close()

    return {
        "status": "executed",
        "result": result
    }
