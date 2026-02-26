from nacl.signing import SigningKey
import base64

def generate_ed25519_keypair():
    signing_key = SigningKey.generate()
    verify_key = signing_key.verify_key

    private_key = base64.b64encode(signing_key.encode()).decode()
    public_key = base64.b64encode(verify_key.encode()).decode()

    return {
        "private_key": private_key,
        "public_key": public_key,
    }
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError


def verify_ed25519_signature(public_key_b64: str, message: bytes, signature_b64: str):
    try:
        public_key = VerifyKey(base64.b64decode(public_key_b64))
        signature = base64.b64decode(signature_b64)

        public_key.verify(message, signature)
        return True

    except BadSignatureError:
        return False
