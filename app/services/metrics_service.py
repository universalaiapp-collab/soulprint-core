from sqlalchemy import text
from app.db import SessionLocal


def increment_metric(org_id: str, metric: str):

    db = SessionLocal()

    try:

        db.execute(
            text("""
            INSERT INTO execution_metrics (org_id)
            VALUES (:org_id)
            ON CONFLICT DO NOTHING
            """),
            {"org_id": org_id}
        )

        db.execute(
            text(f"""
            UPDATE execution_metrics
            SET {metric} = {metric} + 1
            WHERE org_id = :org_id
            """),
            {"org_id": org_id}
        )

        db.commit()

    finally:
        db.close()
