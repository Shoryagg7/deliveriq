"""
Idempotency-Key middleware — safe retries for non-idempotent requests.

A client that POSTs an order, times out, and retries has no way to know whether
the first attempt landed. Without this, the retry creates a SECOND order. With
it, the retry replays the first response and nothing is reprocessed.

Only POST, and only when the header is present: an opt-in contract, so a caller
that doesn't care pays nothing.
"""

import hashlib
import json
import logging

import redis
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.metrics import idempotent_replays_total
from app.core.redis_client import async_redis_client
from app.core.security import subject_from_bearer

logger = logging.getLogger("deliveriq")

IDEMPOTENCY_TTL = 86_400  # 24h — long enough for any sane client retry window


def _namespace(request: Request) -> str:
    """The principal an idempotency key belongs to (G05).

    The key used to be global — `idempotency:{key}` — so two users who both sent
    `Idempotency-Key: retry-1` collided and the second received the FIRST user's
    cached response body. That is a cross-tenant leak, not a correctness nit.

    Derived from the VERIFIED token subject, so a caller cannot pick someone
    else's namespace. Anonymous callers share one bucket, which is safe only
    because the fingerprint below still has to match.
    """
    sub = subject_from_bearer(request.headers.get("Authorization"))
    if sub is None:
        return "anon"
    return hashlib.sha256(sub.encode()).hexdigest()[:32]


def _fingerprint(request: Request, body: bytes) -> str:
    """Hash of what was actually requested.

    An idempotency key promises "this is a retry of that exact call". Without
    binding the key to the request, the same key sent with a DIFFERENT payload
    silently replays the old response — the client gets a confident answer to a
    question it did not ask. Mismatch is a 422, not a replay.
    """
    h = hashlib.sha256()
    h.update(request.method.encode())
    h.update(b"\x00")
    h.update(request.url.path.encode())
    h.update(b"\x00")
    h.update(body)
    return h.hexdigest()


async def idempotency_middleware(request: Request, call_next):
    key = request.headers.get("Idempotency-Key")
    if request.method != "POST" or not key:
        return await call_next(request)

    # Draining the body here would leave the route with an empty stream, so put
    # it back as a fresh receive channel before calling downstream.
    body = await request.body()

    async def _replay_body():
        return {"type": "http.request", "body": body, "more_body": False}

    request._receive = _replay_body  # noqa: SLF001

    cache_key = f"idempotency:{_namespace(request)}:{key}"
    fingerprint = _fingerprint(request, body)

    try:
        cached = await async_redis_client.get(cache_key)
    except redis.RedisError as exc:
        # Fail OPEN: without Redis we cannot dedupe, but refusing traffic would
        # be worse. The client's retry may duplicate — which is exactly why the
        # analytics consumer dedupes independently. Defence at both layers.
        logger.error("idempotency degraded, failing OPEN: %s", exc)
        return await call_next(request)

    if cached is not None:
        record = json.loads(cached)

        if record.get("fingerprint") != fingerprint:
            return JSONResponse(
                status_code=422,
                content={
                    "error": "IDEMPOTENCY_KEY_REUSED",
                    "message": (
                        "This Idempotency-Key was already used for a different "
                        "request. Use a new key for a new request."
                    ),
                },
            )

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
        idempotent_replays_total.inc()
        logger.info("idempotent replay for key=%s", key)
        return Response(
            content=record["body"].encode(),
            status_code=record["status_code"],
            media_type=record["media_type"],
            headers={"Idempotent-Replay": "true"},
        )

    # Claim the key BEFORE doing the work. NX makes this atomic, so two
    # concurrent retries can't both decide they're the first attempt. The TTL is
    # config-driven and sized to outlive the slowest request (G19) — a lock that
    # expires mid-flight lets the retry double-execute, which is the one thing
    # this middleware exists to prevent.
    claimed = await async_redis_client.set(
        cache_key,
        json.dumps({"in_flight": True, "fingerprint": fingerprint}),
        nx=True,
        ex=settings.idempotency_lock_ttl,
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
    response_body = b"".join([chunk async for chunk in response.body_iterator])

    if response.status_code < 400:
        await async_redis_client.set(
            cache_key,
            json.dumps(
                {
                    "status_code": response.status_code,
                    "body": response_body.decode(),
                    "media_type": response.media_type or "application/json",
                    "fingerprint": fingerprint,
                }
            ),
            ex=IDEMPOTENCY_TTL,
        )
    else:
        # Don't cache failures — a retry after a 500 should genuinely re-run.
        await async_redis_client.delete(cache_key)

    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )
