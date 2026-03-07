from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from uuid import uuid4
import hashlib
import secrets
from datetime import datetime
from sqlalchemy import text
import logging

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
from app.routes.analytics import router as analytics_router
from app.routes.ledger import router as ledger_router
from app.routes.dev import router as dev_router

# --------------------------------
# Create FastAPI App
# --------------------------------

app = FastAPI(
    title="Soulprint",
    description="AI Execution Firewall for AI Agents",
    version="1.0.0"
)


# --------------------------------
# Setup Logging
# --------------------------------

setup_logger()
logger = logging.getLogger(__name__)


# --------------------------------
# Register Routers (Versioned API)
# --------------------------------

app.include_router(agents.router, prefix="/v1")
app.include_router(escalation_router, prefix="/v1")
app.include_router(analytics_router, prefix="/v1")
app.include_router(ledger_router, prefix="/v1")
app.include_router(dev_router)

# --------------------------------
# Register Error Handlers
# --------------------------------

app.add_exception_handler(429, rate_limit_handler)
app.add_exception_handler(HTTPException, global_http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)


# --------------------------------
# Request Models
# --------------------------------

class OrgCreateRequest(BaseModel):
    name: str
    tier: str


# --------------------------------
# Create Organization (Public)
# --------------------------------

@app.post("/v1/org/create")
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
            "path": "/v1/org/create",
            "status_code": 200
        }
    )

    return {
        "org_id": org_id,
        "api_key": raw_api_key
    }


# --------------------------------
# Protected Test Route
# --------------------------------

@app.get("/v1/protected")
def protected_route(org_id: str = Depends(get_current_org)):

    logger.info(
        "protected_access",
        extra={
            "org_id": org_id,
            "path": "/v1/protected",
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
