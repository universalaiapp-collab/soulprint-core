from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from sqlalchemy import text

router = APIRouter()


@router.get("/analytics/summary")
def get_summary(db: Session = Depends(get_db)):

    result = db.execute(text("""

        SELECT

        SUM(actions_executed) as actions_executed,
        SUM(loops_blocked) as loops_blocked,
        SUM(duplicate_actions) as duplicate_actions,
        SUM(retry_denied) as retry_denied,
        SUM(escalations_triggered) as escalations_triggered

        FROM execution_metrics

    """)).fetchone()

    return {

        "actions_executed": result[0] or 0,
        "loops_blocked": result[1] or 0,
        "duplicate_actions": result[2] or 0,
        "retry_denied": result[3] or 0,
        "escalations_triggered": result[4] or 0

    }
