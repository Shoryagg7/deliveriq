from fastapi import HTTPException, Request

from app.core.redis_client import redis_client

LIMIT = 5  # max requests
WINDOW = 10  # per 60 seconds


def rate_limiter(request: Request):
    client = request.client
    client_ip = client.host if client is not None else "unknown"
    key = f"ratelimit:{client_ip}"

    count = redis_client.incr(key)
    if count == 1:
        redis_client.expire(key, WINDOW)

    if count > LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Max {LIMIT} per {WINDOW}s.",
        )
