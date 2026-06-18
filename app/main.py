from datetime import datetime, timezone

from fastapi import FastAPI

from app.schemas.order import OrderCreate, OrderResponse

app = FastAPI(title="DeliverIQ")
orders_db = {}
next_id = 1


@app.post("/orders", response_model=OrderResponse, status_code=201)
def create_order(order: OrderCreate):
    global next_id
    new_order = {
        "id": next_id,
        "customer_id": order.customer_id,
        "value": order.value,
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc)
    }
    orders_db[next_id] = new_order
    next_id += 1
    return new_order  # we return EVERYTHING — watch what comes out

