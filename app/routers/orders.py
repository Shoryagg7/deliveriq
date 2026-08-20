from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import (
    assert_may_change_status,
    get_current_user,
    require_ops,
)
from app.core.enums import OrderStatus, UserRole
from app.core.exceptions import NoPendingOrders, OrderNotFound, RiderUnavailable
from app.core.metrics import dispatch_duration_seconds, dispatch_total
from app.models.order import Order
from app.models.rider import Rider
from app.models.user import User
from app.schemas.order import OrderCreate, OrderResponse
from app.services.dispatch import pick_next_order
from app.services.geohash_service import update_rider_location
from app.services.order_state import transition

router = APIRouter(prefix="/orders", tags=["orders"])


def _visible_orders(query, user: User):
    """Narrow a query to what this caller is allowed to see (G03).

    Applied as a WHERE clause rather than a post-filter, so a customer's listing
    never loads another customer's row into memory in the first place.

        ops       — everything
        rider     — only orders assigned to them
        customer  — only their own
    """
    if user.role == UserRole.OPS.value:
        return query
    if user.role == UserRole.RIDER.value:
        # A rider account with no linked record can see nothing rather than
        # everything: `rider_id IS NULL` would match every unassigned order.
        if user.rider_id is None:
            return query.filter(False)
        return query.filter(Order.rider_id == user.rider_id)
    return query.filter(Order.customer_id == user.id)


@router.post("", response_model=OrderResponse, status_code=201)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """The caller places an order AS THEMSELVES (G02).

    `customer_id` is taken from the verified token, not the body. Accepting it
    from the client meant anyone could place an order under any customer id —
    and left the system with no trustworthy notion of ownership at all, which is
    what every read-scoping rule below depends on.
    """
    new_order = Order(**order.model_dump(), customer_id=user.id)
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """404 for an order the caller may not see, not 403.

    Deliberate: 403 would confirm the order EXISTS, letting anyone enumerate
    order ids one request at a time. Here — unlike the rider-location guard —
    hiding existence is the stronger answer, because the id alone is the secret.
    """
    order = _visible_orders(db.query(Order), user).filter(Order.id == order_id).first()
    if not order:
        raise OrderNotFound(f"Order {order_id} not found")
    return order


@router.get("", response_model=list[OrderResponse])
def list_orders(
    status: OrderStatus | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = _visible_orders(db.query(Order), user)
    if status:
        query = query.filter(Order.status == status.value)
    return query.all()


@router.post("/dispatch")
def dispatch_order(
    db: Session = Depends(get_db),
    _: User = Depends(require_ops),
):
    """OPS ONLY. Dispatch assigns work to a courier — it is a fleet
    operation, not something the customer who placed the order or the rider
    who wants it may trigger for themselves. A rider able to call this could
    farm assignments; a customer could jump the queue."""
    # Outcome is labelled, not just counted: "dispatch rate dropped" is useless
    # on its own — no_rider_available (supply problem) and no_pending_orders
    # (demand problem) need opposite responses at 3am.
    with dispatch_duration_seconds.time():
        try:
            result = pick_next_order(db)
        except NoPendingOrders:
            dispatch_total.labels(outcome="no_pending_orders").inc()
            raise
        except RiderUnavailable:
            dispatch_total.labels(outcome="no_rider_available").inc()
            raise
    dispatch_total.labels(outcome="assigned").inc()
    return {"dispatched": result}


class StatusUpdate(BaseModel):
    status: OrderStatus


@router.patch("/{order_id}/status")
def update_status(
    order_id: int,
    body: StatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise OrderNotFound(f"Order {order_id} not found")
    current = OrderStatus(order.status)  # str from DB → enum
    # TWO orthogonal guards, both required:
    #   is this move legal?        PENDING → DELIVERED is not
    #   may THIS caller make it?   a customer marking their own order delivered
    #                              is a legal move by the wrong actor
    assert_may_change_status(user, order, body.status)
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
