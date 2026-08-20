"""HTTP metrics middleware — records every request's outcome and latency."""

import time

from fastapi import Request
from starlette.routing import Match

from app.core.metrics import http_request_duration_seconds, http_requests_total

# Scraping must not inflate what it measures.
_EXCLUDED = frozenset({"/metrics"})


def _route_template(request: Request) -> str:
    """The matched route pattern, never the raw path.

    "/orders/{order_id}" is one time series; "/orders/1", "/orders/2", ... is
    one per order forever. Unmatched paths collapse to a single bucket so a 404
    scanner can't create series either.

    `scope["route"]` is only populated once the ROUTER has matched. Since G16
    moved this middleware outside rate-limiting and idempotency, a 429 or an
    idempotent replay returns before that ever happens — so the template has to
    be resolved here instead. Without this, the fix for "replays are not counted"
    would have shipped a second bug: replays counted under "__unmatched__",
    which is a worse lie than a missing count.
    """
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    if path:
        return path

    for candidate in request.app.routes:
        # Only real endpoints; the StaticFiles Mount at "/" matches everything
        # and would swallow every genuinely unknown path into its own label.
        if not hasattr(candidate, "methods"):
            continue
        match, _ = candidate.matches(request.scope)
        if match is Match.FULL:
            return getattr(candidate, "path", None) or "__unmatched__"
    return "__unmatched__"


async def metrics_middleware(request: Request, call_next):
    if request.url.path in _EXCLUDED:
        return await call_next(request)

    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        # An unhandled exception is still an outcome — record it as 500 rather
        # than losing the request from the metric entirely, then re-raise.
        http_requests_total.labels(
            method=request.method, route=_route_template(request), status="500"
        ).inc()
        raise

    elapsed = time.perf_counter() - start
    route = _route_template(request)
    http_requests_total.labels(
        method=request.method, route=route, status=str(response.status_code)
    ).inc()
    http_request_duration_seconds.labels(method=request.method, route=route).observe(
        elapsed
    )
    return response
