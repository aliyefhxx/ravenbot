"""AES-256-GCM session şifrələmə utility"""
import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def _key() -> bytes:
    k = os.getenv("ENCRYPTION_KEY")
    if not k:
        raise RuntimeError("ENCRYPTION_KEY env yoxdur")
    raw = base64.urlsafe_b64decode(k.encode())
    if len(raw) != 32:
        raise RuntimeError("ENCRYPTION_KEY 32 bayt (base64) olmalıdır")
    return raw

def encrypt(plaintext: str) -> str:
    aes = AESGCM(_key())
    nonce = os.urandom(12)
    ct = aes.encrypt(nonce, plaintext.encode(), None)
    return base64.urlsafe_b64encode(nonce + ct).decode()

def decrypt(token: str) -> str:
    data = base64.urlsafe_b64decode(token.encode())
    nonce, ct = data[:12], data[12:]
    return AESGCM(_key()).decrypt(nonce, ct, None).decode()

def generate_key() -> str:
    return base64.urlsafe_b64encode(os.urandom(32)).decode()

if __name__ == "__main__":
    print(generate_key())
