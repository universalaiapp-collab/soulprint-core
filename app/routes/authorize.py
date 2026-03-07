from app.services.firewall import check_firewall
from app.services.escalation_engine import should_escalate

decision = check_firewall(org_id, agent_id, payload)

if decision != "ALLOW":
    return {"status": decision}

if should_escalate(payload):
    return {"status": "CHALLENGE_HUMAN"}

from app.models.action_memory import ActionMemory
from app.db import SessionLocal

db = SessionLocal()

memory = db.query(ActionMemory).filter(
    ActionMemory.org_id == org_id,
    ActionMemory.agent_id == agent_id
).order_by(ActionMemory.created_at.desc()).first()

memory.completed = True
memory.in_progress = False

db.commit()
