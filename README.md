# Soulprint

**Soulprint is an execution firewall for AI agents.**

It gives **identity, authorization, and safety controls** to AI agents running in production systems.

Human IAM systems manage **people**.

Soulprint governs **machines.**

---

# The Problem

AI agents are starting to perform real-world actions such as:

- sending emails
- executing API calls
- triggering payments
- running workflows
- modifying databases

Without execution control, agents can cause serious failures:

• infinite loops  
• duplicate execution  
• runaway automation  
• dangerous operations  
• massive API cost spikes  

Traditional IAM tools do not protect against these problems.

---

# The Solution

Soulprint introduces a **governance layer for AI agents**.

Every action executed by an agent passes through the **Soulprint Execution Firewall**.

This provides:

• agent identity verification  
• execution authorization  
• loop prevention  
• duplicate protection  
• human escalation  
• tamper-proof decision logging  

Soulprint ensures agents act **safely, deterministically, and auditable**.

---

# Core Capabilities

## Agent Identity

Every AI agent receives a cryptographic identity.

Requests are signed using **ed25519 keys**, ensuring:

- verified agent identity
- tamper-proof requests
- secure execution authorization

---

## Execution Firewall

Before an action executes, Soulprint checks:

- duplicate execution
- retry limits
- infinite loop behavior
- policy violations

Unsafe actions are blocked.

---

## Human Escalation

High-risk actions can require manual approval.

Example:

## Quickstart

Start using Soulprint in 3 steps.

### 1. Create Organization

POST /v1/org/create

Example:

curl -X POST https://soulprint-core-production.up.railway.app/v1/org/create \
-H "Content-Type: application/json" \
-d '{"name":"demo-org","tier":"dev"}'

This returns:

- org_id
- api_key

---

### 2. Create Agent

POST /v1/agents/create

This generates:

- agent_id
- public key
- private key

---

### 3. Execute Secure Action

POST /v1/agents/secure-action

Example payload:

{
  "action_type": "test",
  "message": "hello"
}

Soulprint will:

• verify agent identity  
• check firewall rules  
• record decision in ledger  
• execute action safely

## Example Flow

AI Agent
   ↓
Soulprint SDK
   ↓
Soulprint Execution Firewall
   ↓
Decision Ledger
   ↓
Action Execution
