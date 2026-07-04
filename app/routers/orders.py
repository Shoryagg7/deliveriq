from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import OrderStatus
from app.core.exceptions import OrderNotFound
from app.models.order import Order
from app.models.rider import Rider
from app.schemas.order import OrderCreate, OrderResponse
from app.services.dispatch import pick_next_order
from app.services.geohash_service import update_rider_location
from app.services.order_state import transition

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
        raise OrderNotFound(f"Order {order_id} not found")
    return order


@router.get("", response_model=list[OrderResponse])
def list_orders(status: OrderStatus | None = None, db: Session = Depends(get_db)):
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status.value)
    return query.all()


@router.post("/dispatch")
def dispatch_order(db: Session = Depends(get_db)):
    result = pick_next_order(db)  # raises NoPendingOrders / RiderUnavailable
    return {"dispatched": result}


class StatusUpdate(BaseModel):
    status: OrderStatus


@router.patch("/{order_id}/status")
def update_status(order_id: int, body: StatusUpdate, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise OrderNotFound(f"Order {order_id} not found")
    current = OrderStatus(order.status)  # str from DB → enum
    transition(current, body.status)  # validate; raises InvalidTransition if illegal
    order.status = body.status.value  # type: ignore # enum → str for the DB
    # terminal states free the assigned rider + put them back in the index
    reindex = None
    if body.status in (OrderStatus.DELIVERED, OrderStatus.CANCELLED) and order.rider_id:  # type: ignore
        rider = db.query(Rider).filter(Rider.id == order.rider_id).first()
        if rider:
            rider.status = "AVAILABLE"  # type: ignore
            if body.status == OrderStatus.DELIVERED:
                rider.current_lat = order.drop_lat  # rider is at the drop now
                rider.current_lon = order.drop_lon
            # capture BEFORE commit (attrs expire after); CANCELLED keeps current loc
            reindex = (rider.id, rider.current_lat, rider.current_lon)

    db.commit()

    if reindex:
        update_rider_location(*reindex)  # type: ignore # rider re-enters a geohash cell → selectable

    return {"order_id": order_id, "status": order.status}
