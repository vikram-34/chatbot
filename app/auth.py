"""
Auth / JWT Service
------------------
Handles user signup, password check, and JWT issue/verify.
Corresponds to the "Auth / JWT Service" box under Core Services,
and the "Auth Middleware | JWT Verify" step at the API Gateway.
"""
import hashlib
import hmac
import os
import time
from typing import Optional

from jose import jwt, JWTError

from app.config import settings
from app import storage


def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt.hex() + ":" + digest.hex()


def _verify_password(password: str, stored_hash: str) -> bool:
    salt_hex, digest_hex = stored_hash.split(":")
    salt = bytes.fromhex(salt_hex)
    expected = bytes.fromhex(digest_hex)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return hmac.compare_digest(expected, actual)


def signup(username: str, password: str) -> None:
    if storage.get_user(username):
        raise ValueError("username already exists")
    storage.create_user(username, _hash_password(password))


def authenticate(username: str, password: str) -> bool:
    user = storage.get_user(username)
    if not user:
        return False
    return _verify_password(password, user["password_hash"])


def create_access_token(username: str) -> str:
    payload = {
        "sub": username,
        "exp": time.time() + settings.JWT_EXPIRE_MINUTES * 60,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> Optional[str]:
    """Returns the username if valid, else None. Corresponds to 'JWT Verify' step."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
