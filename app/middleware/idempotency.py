"""
Idempotency-Key middleware — safe retries for non-idempotent requests.

A client that POSTs an order, times out, and retries has no way to know whether
the first attempt landed. Without this, the retry creates a SECOND order. With
it, the retry replays the first response and nothing is reprocessed.

Only POST, and only when the header is present: an opt-in contract, so a caller
that doesn't care pays nothing.
"""

import json
import logging

import redis
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.redis_client import redis_client

logger = logging.getLogger("deliveriq")

IDEMPOTENCY_TTL = 86_400  # 24h — long enough for any sane client retry window
_LOCK_TTL = 30  # seconds a first-attempt claim may hold before it's retryable


async def idempotency_middleware(request: Request, call_next):
    key = request.headers.get("Idempotency-Key")
    if request.method != "POST" or not key:
        return await call_next(request)

    cache_key = f"idempotency:{key}"

    try:
        cached = redis_client.get(cache_key)
    except redis.RedisError as exc:
        # Fail OPEN: without Redis we cannot dedupe, but refusing traffic would
        # be worse. The client's retry may duplicate — which is exactly why the
        # analytics consumer dedupes independently. Defence at both layers.
        logger.error("idempotency degraded, failing OPEN: %s", exc)
        return await call_next(request)

    if cached is not None:
        record = json.loads(cached)
        if record.get("in_flight"):
            # First attempt still running. Returning the half-finished result is
            # impossible, so tell the client to retry rather than double-execute.
            return JSONResponse(
                status_code=409,
                content={
                    "error": "IDEMPOTENCY_IN_PROGRESS",
                    "message": "A request with this Idempotency-Key is still being processed.",
                },
            )
        logger.info("idempotent replay for key=%s", key)
        return Response(
            content=record["body"].encode(),
            status_code=record["status_code"],
            media_type=record["media_type"],
            headers={"Idempotent-Replay": "true"},
        )

    # Claim the key BEFORE doing the work. NX makes this atomic, so two
    # concurrent retries can't both decide they're the first attempt.
    claimed = redis_client.set(
        cache_key, json.dumps({"in_flight": True}), nx=True, ex=_LOCK_TTL
    )
    if not claimed:
        return JSONResponse(
            status_code=409,
            content={
                "error": "IDEMPOTENCY_IN_PROGRESS",
                "message": "A request with this Idempotency-Key is still being processed.",
            },
        )

    response = await call_next(request)

    # BaseHTTPMiddleware hands back a streaming response: `response.body` is not
    # populated, so it must be drained from the iterator — and draining EXHAUSTS
    # it, so the response has to be rebuilt or the client receives an empty body.
    body = b"".join([chunk async for chunk in response.body_iterator])

    if response.status_code < 400:
        redis_client.setex(
            cache_key,
            IDEMPOTENCY_TTL,
            json.dumps(
                {
                    "status_code": response.status_code,
                    "body": body.decode(),
                    "media_type": response.media_type or "application/json",
                }
            ),
        )
    else:
        # Don't cache failures — a retry after a 500 should genuinely re-run.
        redis_client.delete(cache_key)

    return Response(
        content=body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )
