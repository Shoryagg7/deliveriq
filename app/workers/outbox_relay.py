"""Outbox relay — the second half of the transactional outbox.

Dispatch writes events as rows inside its own transaction. This process polls
for unpublished rows, publishes them to Kafka, and marks them done.

Ordering of the two steps is the whole design, and it mirrors the consumer's
commit placement:

    publish -> wait for the broker's ack -> THEN mark published

Marking first would lose the event on a crash in the gap — the same hole the
outbox exists to close, moved one layer down. Publishing first means a crash
before the mark republishes the event: at-least-once, which the consumers
already dedupe on `(partition, offset)`.

`FOR UPDATE SKIP LOCKED` on the claim so several relays can run without two of
them grabbing the same row — the same protocol dispatch uses on orders.
"""

import json
import logging
import signal
import time
from datetime import UTC, datetime
from types import FrameType

from app.core.database import SessionLocal
from app.core.kafka_producer import flush_producer, publish_event
from app.core.logging_config import setup_logging
from app.models.outbox import OutboxEvent

setup_logging()
logger = logging.getLogger("deliveriq.worker")

POLL_SECONDS = 1.0
BATCH = 100
FLUSH_TIMEOUT = 10.0

_running = True


def _request_stop(signum: int, _frame: FrameType | None) -> None:
    global _running
    _running = False
    logger.info("%s received — finishing this batch, then stopping",
                signal.Signals(signum).name)


def drain_once() -> int:
    """Publish one batch. Returns how many were confirmed delivered."""
    db = SessionLocal()
    try:
        rows = (
            db.query(OutboxEvent)
            .filter(OutboxEvent.published_at.is_(None))
            .order_by(OutboxEvent.id)          # oldest first, per-key order kept
            .limit(BATCH)
            .with_for_update(skip_locked=True)  # several relays can run safely
            .all()
        )
        if not rows:
            return 0

        for row in rows:
            publish_event(row.topic, json.loads(row.payload), key=row.key)
            row.attempts = (row.attempts or 0) + 1

        # BLOCK until the broker acks every message in this batch. Marking rows
        # published on an unconfirmed send is exactly the data loss this whole
        # mechanism exists to prevent.
        undelivered = flush_producer(FLUSH_TIMEOUT)
        if undelivered:
            db.rollback()
            logger.error(
                "%d message(s) UNCONFIRMED — leaving batch unpublished for retry",
                undelivered,
            )
            return 0

        stamp = datetime.now(UTC).replace(tzinfo=None)
        for row in rows:
            row.published_at = stamp
        db.commit()
        logger.info("relayed %d event(s)", len(rows))
        return len(rows)
    except Exception:
        db.rollback()
        logger.exception("relay batch failed — rows stay unpublished, will retry")
        return 0
    finally:
        db.close()


def main() -> None:
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)
    logger.info("outbox relay started, polling every %.1fs", POLL_SECONDS)
    while _running:
        if drain_once() == 0:
            time.sleep(POLL_SECONDS)   # nothing to do; don't spin
    flush_producer()
    logger.info("outbox relay stopped cleanly")


if __name__ == "__main__":
    main()
