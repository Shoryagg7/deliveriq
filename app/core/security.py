"""
Password hashing and JWT issue/verify.

bcrypt directly rather than passlib: passlib is unmaintained and breaks against
bcrypt 4.x (it reads a `__about__` attribute that no longer exists). One less
abstraction over a primitive that doesn't need one.
"""

from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"

# bcrypt truncates silently past 72 BYTES — two different long passwords would
# hash identically. Reject instead of truncating, so the limit is the caller's
# problem to see rather than a silent security downgrade.
MAX_PASSWORD_BYTES = 72


class PasswordTooLong(ValueError):
    pass


def hash_password(password: str) -> str:
    raw = password.encode()
    if len(raw) > MAX_PASSWORD_BYTES:
        raise PasswordTooLong(
            f"password must be at most {MAX_PASSWORD_BYTES} bytes (bcrypt limit)"
        )
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    raw = password.encode()
    if len(raw) > MAX_PASSWORD_BYTES:
        return False
    # checkpw is constant-time, so a wrong password costs the same as a right
    # one — no timing signal about which part failed.
    return bcrypt.checkpw(raw, hashed.encode())


def create_access_token(subject: str, is_admin: bool = False) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "is_admin": is_admin,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """Return the claims, or None if the token is invalid/expired/tampered.

    python-jose verifies the signature AND `exp` here — decoding without
    verification (or trusting claims from an unverified decode) is the classic
    JWT hole, since the payload is only base64, not encrypted.
    """
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
    except JWTError:
        return None
