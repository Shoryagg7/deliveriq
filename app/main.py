from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import DeliverIQError
from app.core.logging_config import setup_logging
from app.middleware.rate_limiter import rate_limit_middleware
from app.middleware.request_id import request_id_middleware
from app.models.order import Order  # noqa: F401
from app.models.rider import Rider  # noqa: F401
from app.routers import admin, orders, riders

setup_logging()
app = FastAPI(title="DeliverIQ")
app.include_router(orders.router)
app.include_router(riders.router)
app.include_router(admin.router)
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(request_id_middleware)

import logging  # noqa: E402

logger = logging.getLogger("deliveriq")

@app.get("/health")
def health():
    logger.info("health check hit")
    return {"status": "ok"}


@app.exception_handler(DeliverIQError)
async def deliveriq_error_handler(request: Request, exc: DeliverIQError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.code, "message": exc.message},
    )
