import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass

import settings


API_KEY_PREFIX = "ak_"
SECRET_KEY_PREFIX = "sk_"


@dataclass
class GeneratedCredential:
    plain: str
    prefix: str
    digest: str


def _secret_bytes() -> bytes:
    return settings.JWT_SECRET_KEY.encode("utf-8")


def hash_token(token: str) -> str:
    return hmac.new(_secret_bytes(), token.encode("utf-8"), hashlib.sha256).hexdigest()


def generate_api_key() -> GeneratedCredential:
    plain = f"{API_KEY_PREFIX}{secrets.token_urlsafe(32)}"
    return GeneratedCredential(plain=plain, prefix=plain[:12], digest=hash_token(plain))


def generate_secret_key() -> GeneratedCredential:
    plain = f"{SECRET_KEY_PREFIX}{secrets.token_urlsafe(40)}"
    return GeneratedCredential(plain=plain, prefix=plain[:12], digest=hash_token(plain))


def _xor_stream(length: int) -> bytes:
    seed = _secret_bytes()
    blocks = []
    counter = 0
    while len(b"".join(blocks)) < length:
        blocks.append(hashlib.sha256(seed + counter.to_bytes(8, "big")).digest())
        counter += 1
    return b"".join(blocks)[:length]


def encrypt_secret(secret: str) -> str:
    data = secret.encode("utf-8")
    stream = _xor_stream(len(data))
    cipher = bytes(item ^ key for item, key in zip(data, stream))
    return base64.urlsafe_b64encode(cipher).decode("ascii")


def decrypt_secret(encrypted_secret: str) -> str:
    cipher = base64.urlsafe_b64decode(encrypted_secret.encode("ascii"))
    stream = _xor_stream(len(cipher))
    data = bytes(item ^ key for item, key in zip(cipher, stream))
    return data.decode("utf-8")
