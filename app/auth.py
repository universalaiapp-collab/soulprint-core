import hashlib
import logging
from fastapi import Header, HTTPException
from sqlalchemy import text
from app.db import SessionLocal
from app.core.rate_limit import check_rate_limit

logger = logging.getLogger()

def get_current_org(x_api_key: str = Header(None)):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")

    clean_key = x_api_key.strip()
    key_hash = hashlib.sha256(clean_key.encode()).hexdigest()

    db = SessionLocal()

    result = db.execute(
        text("""
            SELECT org_id, rate_limit_per_sec
            FROM org_api_keys
            JOIN organizations ON organizations.id = org_api_keys.org_id
            WHERE key_hash = :key_hash
            AND is_active = TRUE
        """),
        {"key_hash": key_hash}
    ).fetchone()

    db.close()

    if not result:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    org_id = result[0]
    rate_limit = result[1]

    check_rate_limit(org_id, rate_limit)

    return org_id
