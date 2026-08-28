# app/services/dispatch.py
import json
import time

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.enums import OrderStatus, Topic
from app.core.exceptions import NoPendingOrders, RiderUnavailable
from app.models.order import Order
from app.models.outbox import OutboxEvent
from app.models.rider import Rider
from app.services.geohash_service import (
    record_rider_assignment,
    remove_rider_from_index,
    select_rider,
)
from app.services.order_state import transition

AGING_WEIGHT = 10  # priority points per minute waited — tune this
MAX_ORDERS_SCANNED = 20

# How many orders one dispatch call will try before giving up.
#
# Found by load-testing the CLAIM path (the old benchmark only measured a plain
# INSERT and could never have surfaced this). With a large backlog and no free
# riders, every call walked the ENTIRE pending set before returning 409 — 1,730
# orders scanned to answer "nobody is available", which put dispatch p99 at 11s
# and held row locks the whole way.
#
# If the top N by priority all have no claimable rider, that is a SUPPLY
# problem, and scanning further will not conjure one. Answer fast instead. The
# cost is a rare false 409 when the only free rider is far down the queue —
# cheap, because the caller simply dispatches again.


# priority = value + minutes_waited * AGING_WEIGHT, expressed in SQL.
# `timezone('UTC', now())` yields a naive UTC timestamp, matching how
# created_at is stored — subtracting a tz-aware value from a naive column is a
# silent hour-offset bug waiting to happen.
_PRIORITY = Order.value + (
    func.extract("epoch", func.timezone("UTC", func.now()) - Order.created_at)
    / 60.0
) * AGING_WEIGHT


def _claim_best_order(db: Session, skip_ids: set[int]):
    """Lock the highest-priority claimable PENDING order, or return None.

    The ordering lives in the DATABASE now. It used to load every pending order
    and rebuild an in-process heap on each call — O(n log n) per dispatch, where
    the heap build dominated the O(log n) pop, and n grows with the backlog.
    `ORDER BY ... LIMIT 1` lets Postgres walk an index and stop at the first row
    it can lock, so the work no longer scales with how far behind you are.

    SKIP LOCKED does the contention handling: a row another replica holds is
    invisible rather than blocking, so a contested dispatch degrades into
    "take the next one" instead of queueing behind a lock.
    """
    q = db.query(Order).filter(Order.status == OrderStatus.PENDING.value)
    if skip_ids:
        # Orders already tried this call — we hold their locks and found them no
        # rider, so re-selecting them would spin forever.
        q = q.filter(Order.id.notin_(skip_ids))
    return (
        q.order_by(_PRIORITY.desc())
        .limit(1)
        .with_for_update(skip_locked=True)
        .first()
    )


def pick_next_order(db: Session):
    if (
        db.query(Order.id)
        .filter(Order.status == OrderStatus.PENDING.value)
        .first()
        is None
    ):
        raise NoPendingOrders("No pending orders to dispatch")

    # Walk orders best-first; CLAIM everything before MUTATING anything.
    exhausted: set[int] = set()
    while len(exhausted) < MAX_ORDERS_SCANNED:
        # CLAIM 1 — the order row (exclusive until commit)
        winner = _claim_best_order(db, exhausted)
        if winner is None:
            break  # nothing left we can claim

        order_id = winner.id

        # CLAIM 2 — a rider. Losing a rider must NOT lose the order: on a
        # failed claim (contested by another instance, or stale index entry),
        # exclude that rider and re-select the next-best for THIS order.
        tried: set[int] = set()
        rider = None
        while True:
            rider_id = select_rider(
                winner.pickup_lat, #type: ignore
                winner.pickup_lon, #type: ignore
                exclude=tried,  # type: ignore
            )
            if rider_id is None:
                break  # band exhausted — genuinely nobody for this order

            rider = (
                db.query(Rider)
                .filter(
                    Rider.id == rider_id,
                    Rider.status == "AVAILABLE",
                )
                .with_for_update(skip_locked=True)
                .first()
            )
            if rider is not None:
                break  # rider row locked — exclusively ours until commit
            tried.add(rider_id)  # claim lost — next-best rider, same order

        if rider is None:
            # No claimable rider for THIS order. Mark it so the next iteration
            # doesn't re-select the same row (we still hold its lock) and move
            # on — nothing has been mutated.
            exhausted.add(order_id)
            continue

        # BOTH rows are exclusively ours — only NOW do we mutate
        current = OrderStatus(winner.status)
        transition(current, OrderStatus.ASSIGNED)
        winner.status = OrderStatus.ASSIGNED.value  # type: ignore
        winner.rider_id = rider_id  # type: ignore
        rider.status = "BUSY"  # type: ignore

        # THE OUTBOX WRITE — inside the transaction, not after it.
        #
        # Publishing to Kafka after db.commit() was the dual-write hole: two
        # systems, no shared transaction, so a crash in the gap left the order
        # assigned and the event gone forever. Writing the event as a ROW makes
        # it commit atomically with the order and the rider. The relay publishes
        # it afterwards; if the relay dies mid-publish it republishes, which is
        # at-least-once — already absorbed by the consumers' dedupe on
        # (partition, offset).
        db.add(
            OutboxEvent(
                topic=Topic.ORDER_DISPATCHED.value,
                key=str(order_id),
                payload=json.dumps(
                    {"order_id": order_id, "rider_id": rider_id, "ts": time.time()}
                ),
            )
        )

        db.commit()  # order + rider + event, atomically

        # Redis catch-up AFTER commit only. Redis is derived state and
        # rebuildable, so it does not belong in the outbox.
        remove_rider_from_index(rider_id)
        record_rider_assignment(rider_id)
        return {"order_id": order_id, "rider_id": rider_id}

    raise RiderUnavailable("Orders are pending but no rider is available nearby")
