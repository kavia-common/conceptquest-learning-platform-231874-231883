import base64
import hashlib
import os
from typing import Optional


# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """
    Hash a password using salted SHA-256.

    NOTE: This is a lightweight placeholder approach for the preview system.
    Replace with a strong password hasher (bcrypt/argon2) for production.

    Returns:
        "salt:hash" string.
    """
    salt = os.urandom(16)
    digest = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return f"{base64.b64encode(salt).decode('utf-8')}:{digest}"


# PUBLIC_INTERFACE
def verify_password(password: str, stored: str) -> bool:
    """
    Verify a password against stored "salt:hash".

    Returns:
        True if matches.
    """
    try:
        salt_b64, digest = stored.split(":", 1)
        salt = base64.b64decode(salt_b64.encode("utf-8"))
    except Exception:
        return False
    calc = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return calc == digest


# PUBLIC_INTERFACE
def create_placeholder_token(user_id: int) -> str:
    """
    Create a placeholder token (NOT JWT).

    Returns:
        A simple base64 token encoding user_id and a random suffix.
    """
    raw = f"user:{user_id}:{base64.b64encode(os.urandom(12)).decode('utf-8')}"
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


# PUBLIC_INTERFACE
def parse_placeholder_token(token: str) -> Optional[int]:
    """
    Parse the placeholder token and return user_id if possible.

    Returns:
        user_id if parseable, else None.
    """
    try:
        raw = base64.b64decode(token.encode("utf-8")).decode("utf-8")
        prefix, user_id_str, _ = raw.split(":", 2)
        if prefix != "user":
            return None
        return int(user_id_str)
    except Exception:
        return None
