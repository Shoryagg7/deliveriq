from fastapi import FastAPI, HTTPException

app = FastAPI(title="DeliverIQ")

# Fake in-memory database for now
orders_db = {
    1: {"id": 1, "value": 250, "status": "PENDING"},
    2: {"id": 2, "value": 800, "status": "DELIVERED"},
}


@app.get("/orders/{order_id}")
def get_order(order_id: int):
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail="Order not found")
    return orders_db[order_id]
@app.get("/orders")
def list_orders(status: str | None = None):
    if status:
        return [o for o in orders_db.values() if o["status"] == status]
    return list(orders_db.values())
