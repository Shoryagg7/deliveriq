import logging
import time

import redis
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.metrics import rate_limit_rejections_total
from app.core.redis_client import redis_client

logger = logging.getLogger("deliveriq")

# Probes must never touch a dependency. Otherwise Redis going down fails the
# LIVENESS probe, the orchestrator restarts every container, and one dependency
# outage becomes a total outage — the exact cascade the /health vs /ready split
# exists to prevent.
PROBE_PATHS = frozenset({"/health", "/ready"})

BUCKET_SIZE = settings.rate_limit_capacity  # max tokens the bucket can hold
REFILL_RATE = settings.rate_limit_refill_per_min / 60  # tokens added per second
TTL = 120  # seconds — GC abandoned buckets

# KEYS[1]=bucket key  ARGV: capacity, refill_rate, now, ttl
# Runs atomically in Redis — no interleave between refill/check/decrement.
RATE_LIMIT_LUA = """
local data = redis.call('HMGET', KEYS[1], 'tokens', 'last_refill')
local tokens = tonumber(data[1])
local last = tonumber(data[2])
local cap = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local ttl = tonumber(ARGV[4])

if tokens == nil then
  tokens = cap
  last = now
else
  tokens = math.min(cap, tokens + (now - last) * rate)
end

if tokens < 1 then
  return -1
end

tokens = tokens - 1
redis.call('HSET', KEYS[1], 'tokens', tokens, 'last_refill', now)
redis.call('EXPIRE', KEYS[1], ttl)
return tostring(tokens)
"""

# register the script once at import (returns a callable)
_rate_limit = redis_client.register_script(RATE_LIMIT_LUA)


async def rate_limit_middleware(request: Request, call_next):
    if not settings.rate_limit_enabled:  # toggle off for load tests
        return await call_next(request)

    if request.url.path in PROBE_PATHS:
        return await call_next(request)

    # request.client can be None in raw ASGI / some test setups — guard it.
    client = request.client
    client_ip = client.host if client is not None else "unknown"
    client_key = request.headers.get("X-API-Key") or client_ip
    bucket_key = f"rate_limit:{client_key}"
    now = time.time()

    try:
        result = _rate_limit(
            keys=[bucket_key],
            args=[BUCKET_SIZE, REFILL_RATE, now, TTL],
        )
    except redis.RedisError as exc:
        # FAIL OPEN, deliberately. Fail-closed would mean Redis being down takes
        # the entire API down with it — a protective control causing the outage
        # it exists to prevent. Serving unthrottled traffic is the lesser harm
        # here; for a payment or auth control the trade-off inverts.
        logger.error("rate limiter degraded, failing OPEN: %s", exc)
        return await call_next(request)

    if result == "-1" or result == -1:
        rate_limit_rejections_total.inc()
        return JSONResponse(
            status_code=429, content={"error": "Rate limit exceeded. Try again later."}
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(int(float(result)))
    return response
