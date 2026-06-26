from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import OrderStatus
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderResponse
from app.services.dispatch import pick_next_order
from app.services.order_state import InvalidTransition, transition

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    new_order = Order(**order.model_dump())
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    return order


@router.get("", response_model=list[OrderResponse])
def list_orders(status: OrderStatus | None = None, db: Session = Depends(get_db)):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status.value)
    return query.all()

@router.post("/dispatch")
def dispatch_order(db: Session = Depends(get_db)):
    order_id = pick_next_order(db)
    if order_id is None:
        raise HTTPException(404, "No pending orders to dispatch")
    return {"dispatched_order_id": order_id}


class StatusUpdate(BaseModel):
    status: OrderStatus


@router.patch("/{order_id}/status")
def update_status(order_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")

    current = OrderStatus(order.status)  # str from DB → enum
    try:
        transition(current, body.status)  # validate; raises if illegal
    except InvalidTransition as e:
        raise HTTPException(400, str(e))

    order.status = body.status.value  # type: ignore # enum → str for the DB
    db.commit()
    return {"order_id": order_id, "status": order.status}
