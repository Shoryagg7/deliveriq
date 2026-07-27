"""
Kafka consumer for order.dispatched events.

Day 32 — Part 2c: commit AFTER processing → at-least-once delivery.
The commit placement (after the handler, not before) is the guarantee:
a crash before commit re-delivers the message; a crash after commit is safe.
"""

import json
import logging

from confluent_kafka import Consumer, KafkaError

from app.core.config import settings
from app.core.enums import Topic
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("deliveriq.worker")

CONSUMER_GROUP = "notifications"
# Enum, not a literal: a typo'd topic string auto-creates a silent phantom topic
# and the consumer then waits forever on the wrong log. Same enum the producer
# publishes with, so the two can never drift apart.
TOPIC = Topic.ORDER_DISPATCHED.value


def build_consumer() -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap,
            "group.id": CONSUMER_GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )


def main() -> None:
    consumer = build_consumer()
    consumer.subscribe([TOPIC])
    logger.info(
        f"Consumer joined '{CONSUMER_GROUP}', polling '{TOPIC}'. Ctrl-C to stop."
    )

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error(f"consumer error: {msg.error()}")
                continue

            # --- PROCESS ---
            data = json.loads(msg.value().decode("utf-8"))
            logger.info(
                f"[notify] order {data['order_id']} → rider {data['rider_id']} "
                f"(partition {msg.partition()}, offset {msg.offset()})"
            )

            # --- COMMIT (only after processing succeeded) ---
            # Synchronous commit of THIS message's offset. Placement is the
            # contract: if we crash between PROCESS and here, the offset is
            # never advanced, so on restart we re-read and re-notify
            # (at-least-once). If we moved this ABOVE the log line, a crash in
            # the gap would skip the notification forever (at-most-once).
            consumer.commit(message=msg)

    except KeyboardInterrupt:
        logger.info("Consumer stopping (Ctrl-C).")
    finally:
        consumer.close()
        logger.info("Consumer closed cleanly.")


if __name__ == "__main__":
    main()
