"""
Analytics worker — group `analytics`.

Same topic and same events as `notifications`, but a different group.id, so it
gets its OWN full copy with its OWN committed offsets. It can be down for an
hour, come back, and catch up from where it committed — while `notifications`
never notices. That is the thing Redis Pub/Sub could not do: pub/sub is
broadcast-and-forget, so a subscriber that is down misses the message forever.
"""

import logging
from datetime import UTC, datetime

from confluent_kafka import Message
from sqlalchemy.dialects.postgresql import insert

from app.core.database import SessionLocal
from app.core.logging_config import setup_logging
from app.models.dispatch_event import DispatchEvent
from app.workers.runner import run_consumer

setup_logging()
logger = logging.getLogger("deliveriq.worker")

CONSUMER_GROUP = "analytics"


def handle_event(payload: dict, msg: Message) -> None:
    """Persist one dispatch fact, idempotently.

    ON CONFLICT DO NOTHING against the (partition, offset) unique constraint:
    a redelivered message inserts zero rows instead of double-counting. Doing
    the dedupe in ONE statement matters — a SELECT-then-INSERT would race a
    second worker on the same group and both would decide the row was absent.

    Raising here routes the message to the DLQ.
    """
    stmt = (
        insert(DispatchEvent)
        .values(
            order_id=payload["order_id"],
            rider_id=payload["rider_id"],
            dispatched_at=datetime.fromtimestamp(payload["ts"], UTC).replace(
                tzinfo=None
            ),
            recorded_at=datetime.now(UTC).replace(tzinfo=None),
            kafka_partition=msg.partition(),
            kafka_offset=msg.offset(),
        )
        .on_conflict_do_nothing(constraint="uq_dispatch_event_msg")
    )

    db = SessionLocal()
    try:
        result = db.execute(stmt)
        db.commit()
        inserted = result.rowcount == 1
    finally:
        db.close()

    logger.info(
        f"[analytics] {'recorded' if inserted else 'DUPLICATE ignored'} "
        f"order {payload['order_id']} "
        f"(partition {msg.partition()}, offset {msg.offset()})"
    )


def main() -> None:
    run_consumer(CONSUMER_GROUP, handle_event)


if __name__ == "__main__":
    main()
