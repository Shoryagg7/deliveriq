import re
import uuid

from fastapi import Request

from app.core.request_context import request_id_var

# Conservative on purpose: this value lands in every log line for the request,
# so it must not be able to carry newlines (log injection), unbounded length, or
# anything a log aggregator will choke on.
_SAFE_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


def _incoming_request_id(request: Request) -> str | None:
    """Adopt an upstream trace id when it is well-formed (G17).

    Minting a fresh uuid unconditionally means a request crossing a gateway or
    another service gets a NEW id at every hop, so the trail cannot be followed
    across them — which is the entire point of having one. Validate before
    adopting: this is caller-supplied text going straight into structured logs.
    """
    candidate = request.headers.get("X-Request-ID")
    if candidate and _SAFE_REQUEST_ID.match(candidate):
        return candidate
    return None


async def request_id_middleware(request: Request, call_next):
    request_id = _incoming_request_id(request) or str(uuid.uuid4())
    request_id_var.set(request_id)  # store for this request's context
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
