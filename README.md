# Soulprint

Soulprint is an execution firewall for AI agents.

It provides:
- Multi-tenant API key management
- Per-organization rate limiting
- Key rotation + revocation
- Structured audit logging
- Production-safe error handling

## Why?

Human IAM tools manage users.
Soulprint governs machine execution.

AI agents can:
- Loop infinitely
- Duplicate actions
- Cause cost spikes

Soulprint prevents that.

## Current Features (Phase 0 Complete)

- Organization creation
- Secure API key hashing
- Key rotation
- Per-org Redis rate limiting
- Structured JSON logs

## Roadmap

Phase 1:
- Agent identity
- ed25519 signatures
- Decision ledger

Phase 2:
- Execution firewall
- Loop prevention
- Idempotency control

Phase 3:
- Spending governor
- Budget enforcement
