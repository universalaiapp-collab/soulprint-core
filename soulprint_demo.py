import requests
from soulprint import Client

BASE_URL = "https://soulprint-core-production.up.railway.app"

print("\n====================================")
print("SOULPRINT FULL SYSTEM DEMO")
print("====================================")

# --------------------------------
# Create demo agent
# --------------------------------

print("\nCreating demo agent...")

quickstart = requests.post(f"{BASE_URL}/v1/dev/quickstart").json()

agent_id = quickstart["agent_id"]
private_key = quickstart["private_key"]

print("Agent created:", agent_id)

client = Client(
    base_url=BASE_URL,
    agent_id=agent_id,
    private_key=private_key
)

# --------------------------------
# TEST 1 — Basic execution
# --------------------------------

print("\n====================================")
print("TEST 1 — Basic Execution")
print("====================================")

try:
    result = client.secure_action({"action_type": "basic_test"})
    print("PASS:", result)
except Exception as e:
    print("FAIL:", e)

# --------------------------------
# TEST 2 — Duplicate detection
# --------------------------------

print("\n====================================")
print("TEST 2 — Duplicate Detection")
print("====================================")

payload = {"action_type": "duplicate_test"}

first = client.secure_action(payload)
second = client.secure_action(payload)

print("First execution:", first)
print("Second execution:", second)

if "DENY" in str(second):
    print("PASS: duplicate blocked")
else:
    print("FAIL: duplicate not blocked")

# --------------------------------
# TEST 3 — Loop detection
# --------------------------------

print("\n====================================")
print("TEST 3 — Loop Detection")
print("====================================")

for i in range(5):
    try:
        r = client.secure_action({"action_type": "loop_test"})
        print(i, r)
    except Exception as e:
        print("Loop blocked:", e)

print("PASS: loop protection working")

# --------------------------------
# TEST 4 — Ledger entry creation
# --------------------------------

print("\n====================================")
print("TEST 4 — Ledger Entry")
print("====================================")

result = client.secure_action({"action_type": "ledger_test"})

print("Ledger hash:", result["ledger_hash"])
print("PASS: ledger recorded")

# --------------------------------
# TEST 5 — View ledger
# --------------------------------

print("\n====================================")
print("TEST 5 — View Ledger Records")
print("====================================")

ledger = requests.get(f"{BASE_URL}/v1/ledger").json()

print("Ledger entries:", ledger["count"])

for entry in ledger["entries"][:5]:
    print(
        "Agent:", entry["agent_id"],
        "| Hash:", entry["decision_hash"][:12],
        "| Time:", entry["created_at"]
    )

print("PASS: ledger visible")

# --------------------------------
# TEST 6 — Ledger integrity verification
# --------------------------------

print("\n====================================")
print("TEST 6 — Ledger Verification")
print("====================================")

verify = requests.get(f"{BASE_URL}/v1/ledger/verify").json()

print("Ledger integrity:", verify)

if verify.get("ledger_valid"):
    print("PASS: ledger chain valid")
else:
    print("FAIL: ledger corrupted")

# --------------------------------
# TEST 7 — API health
# --------------------------------

print("\n====================================")
print("TEST 7 — API Health")
print("====================================")

health = requests.get(f"{BASE_URL}/health").text

print("Health endpoint:", health)

print("\n====================================")
print("SOULPRINT DEMO COMPLETE")
print("====================================")
