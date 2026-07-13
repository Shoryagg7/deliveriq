import heapq
import json
import time
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.enums import OrderStatus
from app.core.exceptions import NoPendingOrders, RiderUnavailable
from app.core.redis_client import redis_client
from app.models.order import Order
from app.models.rider import Rider
from app.services.geohash_service import (
    record_rider_assignment,
    remove_rider_from_index,
    select_rider,
)
from app.services.order_state import transition

AGING_WEIGHT = 10  # priority points per minute waited — tune this


def pick_next_order(db: Session):
    pending = db.query(Order).filter(Order.status == OrderStatus.PENDING.value).all()
    if not pending:
        raise NoPendingOrders("No pending orders to dispatch")

    now = datetime.now(UTC).replace(tzinfo=None)
    heap = []
    for order in pending:
        wait_minutes = (now - order.created_at).total_seconds() / 60
        priority = order.value + wait_minutes * AGING_WEIGHT
        heapq.heappush(heap, (-priority, order.id))

    # walk orders best-first; CLAIM everything before MUTATING anything
    while heap:
        neg_priority, order_id = heapq.heappop(heap)

        # CLAIM 1 — the order row (exclusive until commit)
        winner = (
            db.query(Order)
            .filter(
                Order.id == order_id,
                Order.status == OrderStatus.PENDING.value,
            )
            .with_for_update(skip_locked=True)
            .first()
        )
        if winner is None:
            continue  # another instance has it — next candidate

        rider_id = select_rider(winner.pickup_lat, winner.pickup_lon)  # type: ignore
        if rider_id is None:
            continue  # no rider nearby — next candidate (nothing mutated)

        # CLAIM 2 — the rider row (lock + AVAILABLE re-check)
        rider = (
            db.query(Rider)
            .filter(
                Rider.id == rider_id,
                Rider.status == "AVAILABLE",
            )
            .with_for_update(skip_locked=True)
            .first()
        )
        if rider is None:
            continue  # rider taken — next candidate (nothing mutated)

        # BOTH rows are exclusively ours — only NOW do we mutate
        current = OrderStatus(winner.status)
        transition(current, OrderStatus.ASSIGNED)
        winner.status = OrderStatus.ASSIGNED.value  # type: ignore
        winner.rider_id = rider_id  # type: ignore
        rider.status = "BUSY"  # type: ignore

        db.commit()

        # Redis catch-up AFTER commit only
        remove_rider_from_index(rider_id)
        record_rider_assignment(rider_id)
        redis_client.publish(
            "order.dispatched",
            json.dumps({"order_id": order_id, "rider_id": rider_id, "ts": time.time()}),
        )
        return {"order_id": order_id, "rider_id": rider_id}

    raise RiderUnavailable("Orders are pending but no rider is available nearby")
