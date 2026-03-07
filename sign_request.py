import base64
from nacl.signing import SigningKey

# your agent private key
private_key_b64 = "voiV877YK+GLmRSXr8ububiBjoR3kgF0l74oaCXuGak="

# EXACT request body
message = b'{"action":"transfer","amount":100000}'

private_key = base64.b64decode(private_key_b64)

signing_key = SigningKey(private_key)

signature = signing_key.sign(message).signature

signature_b64 = base64.b64encode(signature).decode()

print("\nSIGNATURE:\n")
print(signature_b64)
