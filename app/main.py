# app/main.py
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text

from app.core.database import SessionLocal
from app.core.exceptions import DeliverIQError
from app.core.kafka_producer import flush_producer, get_producer
from app.core.redis_client import redis_client
from app.core.logging_config import setup_logging
from app.core.metrics import dependency_up
from app.middleware.idempotency import idempotency_middleware
from app.middleware.metrics import metrics_middleware
from app.middleware.rate_limiter import rate_limit_middleware
from app.middleware.request_id import request_id_middleware
from app.models.order import Order  # noqa: F401
from app.models.rider import Rider  # noqa: F401
from app.models.user import User  # noqa: F401
from app.routers import admin, auth, orders, riders

setup_logging()
logger = logging.getLogger("deliveriq")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup ---
    yield
    # --- shutdown --- drain buffered events before the process dies
    logger.info("shutdown: flushing kafka producer")
    flush_producer()


app = FastAPI(title="DeliverIQ", lifespan=lifespan)
app.include_router(orders.router)
app.include_router(riders.router)
app.include_router(admin.router)
app.include_router(auth.router)
# Middleware runs in REVERSE registration order, so this list reads
# outermost-last. Effective order per request:
#   request_id  -> rate_limit -> idempotency -> route
# request_id outermost so every log line, including a 429, carries a trace id.
# rate_limit before idempotency so a flood of replayed keys is still throttled.
app.middleware("http")(metrics_middleware)
app.middleware("http")(idempotency_middleware)
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(request_id_middleware)


@app.get("/health")
def health():
    """Liveness only — is this process up? Cheap, no dependencies.

    Kept separate from /ready on purpose: a load balancer that restarts a
    container because Redis blipped turns one dependency outage into an outage
    of everything. Liveness answers "restart me?", readiness answers "route to
    me?" — different questions, different consequences.
    """
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness — can this process actually serve traffic?

    Round-trips every hard dependency rather than checking a cached flag: a
    connection pool can look healthy while the server behind it is gone. Returns
    503 with a per-dependency breakdown so the failing one is named, not guessed.
    """
    checks: dict[str, str] = {}

    try:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            checks["postgres"] = "ok"
        finally:
            db.close()
    except Exception as exc:  # noqa: BLE001 — report, never raise from a probe
        checks["postgres"] = f"error: {type(exc).__name__}"

    try:
        redis_client.ping()
        checks["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["redis"] = f"error: {type(exc).__name__}"

    try:
        # metadata round-trip = the broker answered. list_topics with a short
        # timeout, because a readiness probe that blocks is itself an outage.
        get_producer().list_topics(timeout=2.0)
        checks["kafka"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["kafka"] = f"error: {type(exc).__name__}"

    for dep, verdict in checks.items():
        dependency_up.labels(dependency=dep).set(1 if verdict == "ok" else 0)

    healthy = all(v == "ok" for v in checks.values())
    if not healthy:
        logger.error("readiness FAILED: %s", checks)
    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "degraded", "checks": checks},
    )


@app.get("/metrics")
def metrics():
    """Prometheus scrape target. Deliberately unauthenticated — it is
    reachable only inside the compose network, and putting auth on it means
    the scraper needs credentials it will inevitably have hardcoded."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.exception_handler(DeliverIQError)
async def deliveriq_error_handler(request: Request, exc: DeliverIQError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message},
    )
