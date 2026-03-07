from soulprint import Client

client = Client(
    base_url="https://soulprint-core-production.up.railway.app",
    agent_id="your-agent-id",
    private_key="your-private-key"
)

payload = {
    "action_type": "transfer",
    "amount": 100
}

result = client.secure_action(payload)

print("Result:", result)
