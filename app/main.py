from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from uuid import uuid4
import hashlib
import secrets
from datetime import datetime
from sqlalchemy import text
import logging
from app.routes.analytics import router as analytics_router
from app.routes.ledger import router as ledger_router

# Database
from app.db import SessionLocal

# Auth
from app.auth import get_current_org

# Core utilities
from app.core.exception_handlers import rate_limit_handler
from app.core.logger import setup_logger
from app.core.error_handler import (
    global_http_exception_handler,
    unhandled_exception_handler
)

# Routers
from app.api import agents
from app.routes.escalation import router as escalation_router


# --------------------------------
# Create FastAPI App
# --------------------------------

app = FastAPI()


# --------------------------------
# Setup Logging
# --------------------------------

setup_logger()
logger = logging.getLogger()


# --------------------------------
# Register Routers
# --------------------------------

app.include_router(agents.router)
app.include_router(escalation_router)
app.include_router(analytics_router)
app.include_router(ledger_router)

# --------------------------------
# Register Error Handlers
# --------------------------------

app.add_exception_handler(429, rate_limit_handler)
app.add_exception_handler(HTTPException, global_http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


# --------------------------------
# Request Model
# --------------------------------

class OrgCreateRequest(BaseModel):
    name: str
    tier: str


# --------------------------------
# Create Organization (Public)
# --------------------------------

@app.post("/org/create")
def create_org(request: OrgCreateRequest):

    db = SessionLocal()

    org_id = str(uuid4())
    raw_api_key = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_api_key.encode()).hexdigest()
    now = datetime.utcnow()

    db.execute(
        text("""
            INSERT INTO organizations
            (id, name, tier, rate_limit_per_sec, monthly_action_limit, created_at)
            VALUES (:id, :name, :tier, :rate, :limit, :created)
        """),
        {
            "id": org_id,
            "name": request.name,
            "tier": request.tier,
            "rate": 5,
            "limit": 10000,
            "created": now
        }
    )

    db.execute(
        text("""
            INSERT INTO org_api_keys
            (id, org_id, key_hash, is_active, created_at)
            VALUES (:id, :org_id, :key_hash, :active, :created)
        """),
        {
            "id": str(uuid4()),
            "org_id": org_id,
            "key_hash": key_hash,
            "active": True,
            "created": now
        }
    )

    db.commit()
    db.close()

    logger.info(
        "org_created",
        extra={
            "org_id": org_id,
            "path": "/org/create",
            "status_code": 200
        }
    )

    return {
        "org_id": org_id,
        "api_key": raw_api_key
    }


# --------------------------------
# Protected Route
# --------------------------------

@app.get("/protected")
def protected_route(org_id: str = Depends(get_current_org)):

    logger.info(
        "protected_access",
        extra={
            "org_id": org_id,
            "path": "/protected",
            "status_code": 200
        }
    )

    return {
        "message": "Access granted",
        "org_id": org_id
    }


# --------------------------------
# Health Check
# --------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}
