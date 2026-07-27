"""
Kafka consumer for order.dispatched events.

Day 32 — Part 2c: commit AFTER processing → at-least-once delivery.
The commit placement (after the handler, not before) is the guarantee:
a crash before commit re-delivers the message; a crash after commit is safe.

Two consequences of that guarantee are handled explicitly below:
  * a message that can NEVER be processed would otherwise block its partition
    forever — it goes to a dead-letter topic instead (see _to_dead_letter);
  * a hard kill never leaves the group cleanly, so the next instance idles for
    session.timeout.ms (~45s) — SIGTERM is caught and drained instead.
"""

import json
import logging
import signal
import time
from types import FrameType

from confluent_kafka import Consumer, KafkaError, Message

from app.core.config import settings
from app.core.enums import Topic
from app.core.kafka_producer import flush_producer, publish_event
from app.core.logging_config import setup_logging

setup_logging()
logger = logging.getLogger("deliveriq.worker")

CONSUMER_GROUP = "notifications"
# Enum, not a literal: a typo'd topic string auto-creates a silent phantom topic
# and the consumer then waits forever on the wrong log. Same enum the producer
# publishes with, so the two can never drift apart.
TOPIC = Topic.ORDER_DISPATCHED.value
DLQ_TOPIC = Topic.ORDER_DISPATCHED_DLQ.value

# How long to wait for the DLQ publish to be acked before giving up on it.
DLQ_FLUSH_TIMEOUT = 10.0

_running = True


def _request_stop(signum: int, _frame: FrameType | None) -> None:
    """Ask the loop to finish the current message and exit through `finally`.

    SIGTERM is what `docker compose stop` and Kubernetes send, and Python does
    NOT turn it into KeyboardInterrupt — without this handler the process dies
    mid-loop, `consumer.close()` never runs, and the group keeps the dead
    member's partitions until session.timeout.ms expires (~45s of a replacement
    instance sitting idle on every single deploy).
    """
    global _running
    _running = False
    logger.info("%s received — finishing current message, then stopping",
                signal.Signals(signum).name)


def build_consumer() -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap,
            "group.id": CONSUMER_GROUP,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )


def handle_event(msg: Message) -> None:
    """Process one message. Raising from here routes it to the DLQ."""
    data = json.loads(msg.value().decode("utf-8"))
    logger.info(
        f"[notify] order {data['order_id']} → rider {data['rider_id']} "
        f"(partition {msg.partition()}, offset {msg.offset()})"
    )


def _to_dead_letter(msg: Message, exc: Exception) -> bool:
    """Park an unprocessable message. Returns True only once it is DURABLE.

    Order matters: publish, then BLOCK until the broker acks, and only then let
    the caller commit. Committing on an unacked DLQ publish would advance past
    the message with no copy of it anywhere — the one way this design can
    actually lose data.
    """
    publish_event(
        DLQ_TOPIC,
        {
            "original_topic": msg.topic(),
            "partition": msg.partition(),
            "offset": msg.offset(),
            "key": msg.key().decode() if msg.key() else None,
            "raw_value": msg.value().decode("utf-8", errors="replace"),
            "error": f"{type(exc).__name__}: {exc}",
            "failed_at": time.time(),
        },
        key=msg.key().decode() if msg.key() else None,
    )
    return flush_producer(DLQ_FLUSH_TIMEOUT) == 0


def main() -> None:
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)

    consumer = build_consumer()
    consumer.subscribe([TOPIC])
    logger.info(
        f"Consumer joined '{CONSUMER_GROUP}', polling '{TOPIC}'. Ctrl-C to stop."
    )

    try:
        while _running:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error(f"consumer error: {msg.error()}")
                continue

            # --- PROCESS ---
            try:
                handle_event(msg)
            except Exception as exc:  # noqa: BLE001 — any failure must be caught
                # Without this, an unprocessable message kills the process
                # before the commit, and the restart re-reads the SAME message
                # forever: the partition is wedged and every valid event queued
                # behind it is never delivered. Lag monitoring does not show it,
                # because a partition with no committed offset has no lag row.
                logger.exception(
                    "unprocessable message → DLQ (partition %s, offset %s)",
                    msg.partition(),
                    msg.offset(),
                )
                if not _to_dead_letter(msg, exc):
                    # DLQ publish not acked. Do NOT commit — stop instead, so
                    # the message is redelivered rather than silently dropped.
                    logger.critical(
                        "DLQ publish UNCONFIRMED — stopping without committing "
                        "so the message is redelivered, not lost"
                    )
                    break

            # --- COMMIT (only after processing succeeded, or the message was
            # safely parked in the DLQ) ---
            # Placement is the contract: if we crash between PROCESS and here,
            # the offset is never advanced, so on restart we re-read and
            # re-notify (at-least-once). If we moved this ABOVE the handler, a
            # crash in the gap would skip the notification forever
            # (at-most-once).
            consumer.commit(message=msg)

    except KeyboardInterrupt:  # pragma: no cover — SIGINT is handled above
        logger.info("Consumer stopping (Ctrl-C).")
    finally:
        flush_producer()
        consumer.close()
        logger.info("Consumer closed cleanly.")


if __name__ == "__main__":
    main()
