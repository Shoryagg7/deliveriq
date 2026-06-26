import heapq

from sqlalchemy.orm import Session

from app.core.enums import OrderStatus
from app.models.order import Order


def pick_next_order(db: Session):
    # 1. Pull only orders still waiting for a rider
    pending = db.query(Order).filter(Order.status == OrderStatus.PENDING.value).all()

    if not pending:
        return None  # nothing to dispatch

    # 2. Build the heap: (-value, id) so highest value pops first
    heap = []
    for order in pending:
        heapq.heappush(heap, (-order.value, order.id))

    # 3. Pop the winner
    neg_value, order_id = heapq.heappop(heap)
    by_id = {o.id: o for o in pending}
    winner = by_id[order_id]
    winner.status = OrderStatus.ASSIGNED.value # pyright: ignore[reportAttributeAccessIssue]
    db.commit()

    return order_id
