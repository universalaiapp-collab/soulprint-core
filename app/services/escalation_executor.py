from sqlalchemy.orm import Session
from app.models.escalation import Escalation
from app.services.secure_action import secure_action_pipeline


def execute_approved(escalation_id: str, db: Session):

    escalation = db.query(Escalation).filter(
        Escalation.id == escalation_id
    ).first()

    if not escalation:
        raise Exception("Escalation not found")

    if escalation.status == "executed":
        raise Exception("Escalation already executed")

    if escalation.status != "approved":
        raise Exception("Escalation must be approved before execution")

    payload = escalation.payload

    try:
        result = secure_action_pipeline(
            org_id=escalation.org_id,
            agent_id=escalation.agent_id,
            payload=payload,
            db=db
        )

        escalation.status = "executed"

        db.commit()

        return {
            "execution_status": "success",
            "result": result
        }

    except Exception as e:

        db.rollback()

        raise Exception(f"Execution failed: {str(e)}")
