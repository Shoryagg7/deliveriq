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
from app.services.geohash_service import remove_rider_from_index, select_rider
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

    by_id = {o.id: o for o in pending}

    # walk orders in priority order; assign the first one that HAS a rider
    while heap:
        neg_priority, order_id = heapq.heappop(heap)
        winner = by_id[order_id]
        rider_id = select_rider(winner.pickup_lat, winner.pickup_lon)  # type: ignore
        if rider_id is None:
            continue  # no rider for this order — try the next

        current = OrderStatus(winner.status)
        transition(current, OrderStatus.ASSIGNED)
        winner.status = OrderStatus.ASSIGNED.value  # type: ignore
        winner.rider_id = rider_id  # type: ignore

        # rider goes BUSY: Postgres truth + Redis mirror (out of geohash cells)
        rider = db.query(Rider).filter(Rider.id == rider_id).first()
        rider.status = "BUSY"  # type: ignore
        remove_rider_from_index(rider_id)

        db.commit()

        redis_client.publish(
            "order.dispatched",
            json.dumps({"order_id": order_id, "rider_id": rider_id, "ts": time.time()}),
        )
        return {"order_id": order_id, "rider_id": rider_id}

    # orders exist but none had an available rider
    raise RiderUnavailable("Orders are pending but no rider is available nearby")
