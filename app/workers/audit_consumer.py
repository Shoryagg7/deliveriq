"""
Audit worker — group `audit`.

Third group on the same topic. Appends an immutable line per event. Kept
deliberately dumb (no DB, no network) so that when `analytics` or the database
is down, this one keeps running — three groups, three independent failure
domains, one log.
"""

import json
import logging
from datetime import UTC, datetime

from confluent_kafka import Message

from app.core.config import settings
from app.core.logging_config import setup_logging
from app.workers.runner import run_consumer

setup_logging()
logger = logging.getLogger("deliveriq.worker")

CONSUMER_GROUP = "audit"


def handle_event(payload: dict, msg: Message) -> None:
    """Append one audit line. Raising here routes the message to the DLQ."""
    line = {
        "order_id": payload["order_id"],
        "rider_id": payload["rider_id"],
        "dispatched_ts": payload["ts"],
        "partition": msg.partition(),
        "offset": msg.offset(),
        "audited_at": datetime.now(UTC).isoformat(),
    }
    # append-only, flushed per line: an audit trail that buffers is not one
    with open(settings.audit_log_path, "a") as fh:
        fh.write(json.dumps(line) + "\n")
        fh.flush()

    logger.info(
        f"[audit] order {payload['order_id']} → {settings.audit_log_path} "
        f"(partition {msg.partition()}, offset {msg.offset()})"
    )


def main() -> None:
    run_consumer(CONSUMER_GROUP, handle_event)


if __name__ == "__main__":
    main()
