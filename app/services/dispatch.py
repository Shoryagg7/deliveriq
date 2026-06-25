import heapq

from sqlalchemy.orm import Session

from app.models.order import Order


def pick_next_order(db: Session):
    # 1. Pull only orders still waiting for a rider
    pending = db.query(Order).filter(Order.status == "PENDING").all()

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
    winner.status = "ASSIGNED"  # type: ignore
    db.commit()

    return order_id
