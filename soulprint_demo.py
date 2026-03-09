import requests
import time
from soulprint import Client

BASE_URL = "https://soulprint-core-production.up.railway.app"

print("\n====================================")
print("SOULPRINT FULL SYSTEM DEMO")
print("====================================")

print("\nCreating demo agent...")

# create new agent so duplicates don't interfere
quickstart = requests.post(f"{BASE_URL}/v1/dev/quickstart").json()

AGENT_ID = quickstart["agent_id"]
PRIVATE_KEY = quickstart["private_key"]

print("Agent created:", AGENT_ID)

client = Client(
    base_url=BASE_URL,
    agent_id=AGENT_ID,
    private_key=PRIVATE_KEY
)

print("\n====================================")
print("TEST 1 — Basic Execution")
print("====================================")

try:
    r = client.secure_action({"action_type": "demo"})
    print("PASS:", r)
except Exception as e:
    print("FAIL:", e)

time.sleep(1)

print("\n====================================")
print("TEST 2 — Duplicate Detection")
print("====================================")

payload = {"action_type": "duplicate_demo"}

try:
    r1 = client.secure_action(payload)
    print("First execution:", r1)

    r2 = client.secure_action(payload)
    print("Second execution:", r2)

    if "DENY" in str(r2):
        print("PASS: duplicate blocked")
    else:
        print("FAIL: duplicate allowed")

except Exception as e:
    print("FAIL:", e)

time.sleep(1)

print("\n====================================")
print("TEST 3 — Loop Detection")
print("====================================")

blocked = False

for i in range(5):
    try:
        r = client.secure_action({"action_type": "loop_demo"})
        print(i, r)

        if "DENY" in str(r):
            blocked = True

    except Exception as e:
        print("blocked:", e)
        blocked = True

if blocked:
    print("PASS: loop protection working")
else:
    print("WARNING: loop protection not triggered")

time.sleep(1)

print("\n====================================")
print("TEST 4 — Ledger Entry")
print("====================================")

try:
    r = client.secure_action({"action_type": "ledger_test"})
    print("Ledger hash:", r.get("ledger_hash"))
    print("PASS: ledger recorded")
except Exception as e:
    print("FAIL:", e)

print("\n====================================")
print("TEST 5 — API Health")
print("====================================")

health = requests.get(f"{BASE_URL}/health")

print("Health endpoint:", health.text)

print("\n====================================")
print("SOULPRINT DEMO COMPLETE")
print("====================================")
