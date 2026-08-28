"""Token revocation — the missing half of stateless auth.

A JWT is valid until it expires. Nothing about verifying a signature can express
"this specific token was logged out", so a stolen token stays good for the rest
of its lifetime. The standard fix is a denylist keyed on the token's `jti`,
which is why `create_access_token` mints one.

**Why this doesn't undo statelessness.** The denylist only has to hold a jti
until the token would have expired anyway — an hour here. That is a bounded,
self-cleaning set, not a session store that grows forever, and any replica can
read it. Verification is still local; only the "was this revoked" check is shared.
"""

import logging
from datetime import UTC, datetime

import redis

from app.core.redis_client import redis_client

logger = logging.getLogger("deliveriq")


def _key(jti: str) -> str:
    return f"revoked_jti:{jti}"


def revoke(jti: str, exp: int | None) -> None:
    """Deny this token until it would have expired on its own.

    TTL comes from the token's own `exp`: holding it one second longer is wasted
    memory, one second less reopens the hole. If `exp` is missing or already
    past, there is nothing left to revoke.
    """
    if not jti:
        return
    remaining = int(exp - datetime.now(UTC).timestamp()) if exp else 0
    if remaining <= 0:
        return
    # set(ex=) rather than the deprecated setex; same single round trip.
    redis_client.set(_key(jti), "1", ex=remaining)


def is_revoked(jti: str | None) -> bool:
    """True if this token was logged out.

    FAILS CLOSED — deliberately, and opposite to the rate limiter. If Redis is
    unreachable we cannot prove a token is still valid, and the whole point of
    this check is to stop a *stolen* token. Failing open would reopen that hole
    at exactly the moment the system is already degraded. The rate limiter fails
    open because unthrottled traffic beats an outage; here the trade inverts,
    and being able to say why is the entire lesson.
    """
    if not jti:
        # A token minted before jti existed. Treat as live rather than locking
        # out every session on deploy; they expire within the hour anyway.
        return False
    try:
        return redis_client.exists(_key(jti)) == 1
    except redis.RedisError as exc:
        logger.error("revocation check degraded, failing CLOSED: %s", exc)
        return True
