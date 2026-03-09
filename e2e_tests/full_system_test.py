import requests
from soulprint import Client

BASE_URL = "https://soulprint-core-production.up.railway.app"

# paste credentials from quickstart
AGENT_ID = "edc523b1-f576-4b9d-8f20-369a7612631f"
PRIVATE_KEY = "ccUd9rPk7fzl5cEiUCdlplAjqrZJYVq48GpBW0PIa+U="

client = Client(
    base_url=BASE_URL,
    agent_id=AGENT_ID,
    private_key=PRIVATE_KEY
)

print("\n============================")
print("TEST 1 — Duplicate Detection")
print("============================")

payload = {"action_type": "duplicate_test"}

print(client.secure_action(payload))
print(client.secure_action(payload))


print("\n============================")
print("TEST 2 — Loop Detection")
print("============================")

for i in range(5):
    try:
        print(client.secure_action({"action_type": "loop_test"}))
    except Exception as e:
        print("Loop blocked:", e)


print("\n============================")
print("TEST 3 — Escalation Gate")
print("============================")

try:
    result = client.secure_action({
        "action_type": "dangerous_operation",
        "amount": 1000000
    })
    print(result)
except Exception as e:
    print("Escalation triggered:", e)


print("\n============================")
print("TEST 4 — Suspend Agent")
print("============================")

suspend = requests.post(
    f"{BASE_URL}/agents/suspend",
    json={"agent_id": AGENT_ID}
)

print("Suspend response:", suspend.text)

try:
    print(client.secure_action({"action_type": "test_after_suspend"}))
except Exception as e:
    print("Agent correctly blocked:", e)


print("\n============================")
print("TEST 5 — Ledger Verification")
print("============================")

ledger = requests.get(f"{BASE_URL}/ledger/verify")

print("Ledger status:", ledger.text)

print("\nALL TESTS COMPLETED")
