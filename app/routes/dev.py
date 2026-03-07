from fastapi import APIRouter
from uuid import uuid4
from datetime import datetime
import secrets
import hashlib
import base64

from nacl.signing import SigningKey
from sqlalchemy import text
from app.db import SessionLocal

router = APIRouter(prefix="/v1/dev", tags=["dev"])


@router.post("/quickstart")
def quickstart():

    db = SessionLocal()

    try:

        org_id = str(uuid4())
        agent_id = str(uuid4())

        raw_api_key = secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(raw_api_key.encode()).hexdigest()

        signing_key = SigningKey.generate()
        verify_key = signing_key.verify_key

        private_key = base64.b64encode(signing_key.encode()).decode()
        public_key = base64.b64encode(verify_key.encode()).decode()

        now = datetime.utcnow()

        # create org
        db.execute(
            text("""
            INSERT INTO organizations
            (id, name, tier, created_at)
            VALUES (:id, :name, :tier, :created)
            """),
            {
                "id": org_id,
                "name": "quickstart-org",
                "tier": "dev",
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

        # create agent
        db.execute(
            text("""
            INSERT INTO agents
            (
            id,
            org_id,
            name,
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
            :name,
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
        "name": "quickstart-agent",
        "public_key": public_key,
        "created": now
    }
    )
