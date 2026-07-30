"""
Notification worker — group `notifications`.

Day 32 built this as a standalone loop; Day 33 moved the loop into
runner.run_consumer so `analytics` and `audit` share it. Behaviour is
unchanged: commit AFTER processing → at-least-once, unprocessable messages
to the DLQ, graceful SIGTERM.
"""

import logging

from confluent_kafka import Message

from app.core.logging_config import setup_logging
from app.workers.runner import run_consumer

setup_logging()
logger = logging.getLogger("deliveriq.worker")

CONSUMER_GROUP = "notifications"


def handle_event(payload: dict, msg: Message) -> None:
    """Pretend to send a push notification."""
    logger.info(
        f"[notify] order {payload['order_id']} → rider {payload['rider_id']} "
        f"(partition {msg.partition()}, offset {msg.offset()})"
    )


def main() -> None:
    run_consumer(CONSUMER_GROUP, handle_event)


if __name__ == "__main__":
    main()
