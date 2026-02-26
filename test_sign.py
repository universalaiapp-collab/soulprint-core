from nacl.signing import SigningKey
import base64
import requests
import json

PRIVATE_KEY = "CJLuUAL39u/94beWU9Rhu+Zih0zZD76Gg3UJ8wXs93w="
AGENT_ID = "2ea50945-f2c9-4e06-a4f8-387d8913364e"

signing_key = SigningKey(base64.b64decode(PRIVATE_KEY))

payload = {"hello": "world"}
message = json.dumps(payload).encode()

signature = signing_key.sign(message).signature
signature_b64 = base64.b64encode(signature).decode()

headers = {
    "X-Agent-Id": AGENT_ID,
    "X-Agent-Signature": signature_b64,
    "X-Idempotency-Key": "test-001"
}

r = requests.post(
    "http://127.0.0.1:8000/agents/secure-action",
    json=payload,
    headers=headers
)

print(r.json())
