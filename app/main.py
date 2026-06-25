from fastapi import FastAPI

from app.core.database import Base, engine
from app.middleware.rate_limiter import rate_limit_middleware
from app.models.order import Order  # noqa: F401
from app.models.rider import Rider  # noqa: F401
from app.routers import orders, riders

app = FastAPI(title="DeliverIQ")
app.include_router(orders.router)
app.include_router(riders.router)
app.middleware("http")(rate_limit_middleware)
@app.get("/health")
def health():
    return {"status": "ok"}
