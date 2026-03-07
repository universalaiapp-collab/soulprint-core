from sqlalchemy.orm import Session
from app.models.metrics import ExecutionMetrics


def increment_metric(org_id, field, db: Session):

    metrics = db.query(ExecutionMetrics).filter(
        ExecutionMetrics.org_id == org_id
    ).first()

    if not metrics:

        metrics = ExecutionMetrics(org_id=org_id)

        db.add(metrics)

        db.commit()

        db.refresh(metrics)

    current_value = getattr(metrics, field)

    setattr(metrics, field, current_value + 1)

    db.commit()
