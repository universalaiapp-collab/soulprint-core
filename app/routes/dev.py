from fastapi import APIRouter
from uuid import uuid4
from datetime import datetime
import secrets
import hashlib
from sqlalchemy import text

from app.db import SessionLocal

router = APIRouter(prefix="/v1/dev", tags=["dev"])


@router.post("/quickstart")
def quickstart():

    db = SessionLocal()

    org_id = str(uuid4())
    agent_id = str(uuid4())

    raw_api_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_api_key.encode()).hexdigest()

    private_key = secrets.token_urlsafe(32)
    public_key = hashlib.sha256(private_key.encode()).hexdigest()

    now = datetime.utcnow()

    # create org
    db.execute(
        text("""
        INSERT INTO organizations
        (id, name, tier, rate_limit_per_sec, monthly_action_limit, created_at)
        VALUES (:id, :name, :tier, :rate, :limit, :created)
        """),
        {
            "id": org_id,
            "name": "quickstart-org",
            "tier": "dev",
            "rate": 10,
            "limit": 10000,
            "created": now
        }
    )

    # api key
    db.execute(
        text("""
        INSERT INTO org_api_keys
        (id, org_id, key_hash, is_active, created_at)
        VALUES (:id, :org_id, :key_hash, true, :created)
        """),
        {
            "id": str(uuid4()),
            "org_id": org_id,
            "key_hash": key_hash,
            "created": now
        }
    )

    # agent
    db.execute(
    text("""
    INSERT INTO agents
    (
        id,
        org_id,
        public_key,
        scope_version,
        agent_status,
        expiry_at,
        last_hash,
        created_at
    )
    VALUES
    (
        :id,
        :org_id,
        :public_key,
        1,
        'active',
        NULL,
        '',
        :created
    )
    """),
    {
        "id": agent_id,
        "org_id": org_id,
        "public_key": public_key,
        "created": now
    }
       )

    db.commit()
    db.close()

    return {
        "org_id": org_id,
        "api_key": raw_api_key,
        "agent_id": agent_id,
        "private_key": private_key,
        "base_url": "https://soulprint-core-production.up.railway.app"
    }
