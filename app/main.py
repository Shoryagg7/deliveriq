from fastapi import FastAPI

from app.core.database import Base, engine
from app.models.order import Order
from app.routers import orders

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DeliverIQ")
app.include_router(orders.router)


@app.get("/health")
def health():
    return {"status": "ok"}
