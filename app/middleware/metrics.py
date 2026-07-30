"""HTTP metrics middleware — records every request's outcome and latency."""

import time

from fastapi import Request

from app.core.metrics import http_request_duration_seconds, http_requests_total

# Scraping must not inflate what it measures.
_EXCLUDED = frozenset({"/metrics"})


def _route_template(request: Request) -> str:
    """The matched route pattern, never the raw path.

    "/orders/{order_id}" is one time series; "/orders/1", "/orders/2", ... is
    one per order forever. Unmatched paths collapse to a single bucket so a 404
    scanner can't create series either.
    """
    route = request.scope.get("route")
    return getattr(route, "path", None) or "__unmatched__"


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
