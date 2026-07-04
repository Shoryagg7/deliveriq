import time

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.redis_client import redis_client

BUCKET_SIZE = settings.rate_limit_capacity  # max tokens the bucket can hold
REFILL_RATE = settings.rate_limit_refill_per_min / 60  # tokens added per second


async def rate_limit_middleware(request: Request, call_next):
    if not settings.rate_limit_enabled:  # toggle off for load tests
        return await call_next(request)

    client_key = request.headers.get("X-API-Key") or request.client.host  # type: ignore
    bucket_key = f"rate_limit:{client_key}"
    now = time.time()

    data = redis_client.hgetall(bucket_key)
    if not data:
        # first time we've seen this client → full bucket
        tokens = float(BUCKET_SIZE)
        last_refill = now
    else:
        # refill based on time elapsed since last seen
        tokens = float(data["tokens"])
        last_refill = float(data["last_refill"])
        elapsed = now - last_refill
        tokens = min(BUCKET_SIZE, tokens + elapsed * REFILL_RATE)

    if tokens < 1:
        return JSONResponse(
            status_code=429, content={"error": "Rate limit exceeded. Try again later."}
        )

    tokens -= 1
    redis_client.hset(bucket_key, mapping={"tokens": tokens, "last_refill": now})
    redis_client.expire(bucket_key, 120)

    response = await call_next(request)
    response.headers["X-RateLimit-Remaining"] = str(int(tokens))
    return response
