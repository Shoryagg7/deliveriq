"""
Password hashing and JWT issue/verify.

bcrypt directly rather than passlib: passlib is unmaintained and breaks against
bcrypt 4.x (it reads a `__about__` attribute that no longer exists). One less
abstraction over a primitive that doesn't need one.
"""

import uuid
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
    """Mint a token. Every one carries a `jti` so it can be revoked.

    Without a unique id per token there is nothing to put on a denylist — you
    could only revoke "every token for this user", which logs them out of every
    device to end one session.
    """
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "is_admin": is_admin,
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
        "jti": uuid.uuid4().hex,
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


def subject_from_bearer(authorization: str | None) -> str | None:
    """The verified `sub` from an Authorization header, or None.

    Used by middleware, which runs BEFORE the dependency graph and so has no
    `get_current_user` to lean on. Verification still happens — an unverified
    decode would let a caller pick their own rate-limit bucket or idempotency
    namespace by editing base64, which is the whole hole this closes (G13/G05).

    Returns None rather than raising: middleware must not turn a malformed
    token into an error, only into "unauthenticated". The routes decide that.
    """
    if not authorization or not authorization.startswith("Bearer "):
        return None
    claims = decode_access_token(authorization[7:])
    if claims is None:
        return None
    sub = claims.get("sub")
    return sub if isinstance(sub, str) and sub else None
