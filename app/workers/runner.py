"""
Shared Kafka consumer loop.

Day 33 — three workers read the SAME topic under three different group.ids.
Everything except the handler is identical, so it lives here once: the group
config, the three-way poll guard, dead-lettering, commit-after-processing, and
graceful shutdown. A bug fixed here is fixed for every worker; a loop copied
three times would drift three ways.

The group.id is the whole architecture switch:
  same group.id      -> members split the partitions   (work queue)
  different group.id -> each gets every event          (fan-out)
"""

import json
import logging
import signal
import time
from collections.abc import Callable
from types import FrameType

from confluent_kafka import Consumer, KafkaError, Message

from app.core.config import settings
from app.core.enums import Topic
from app.core.kafka_producer import flush_producer, publish_event

logger = logging.getLogger("deliveriq.worker")

# How long to wait for the DLQ publish to be acked before giving up on it.
DLQ_FLUSH_TIMEOUT = 10.0

# handler(payload, msg) -> None. Raising routes the message to the DLQ.
Handler = Callable[[dict, Message], None]

_running = True


def _request_stop(signum: int, _frame: FrameType | None) -> None:
    """Finish the current message, then exit through `finally`.

    SIGTERM is what `docker compose stop` sends, and Python does NOT turn it
    into KeyboardInterrupt. Without this the process dies mid-loop, close()
    never runs, and the group holds the dead member's partitions until
    session.timeout.ms expires — measured at 44.7s of a replacement instance
    sitting idle, on every deploy.
    """
    global _running
    _running = False
    logger.info(
        "%s received — finishing current message, then stopping",
        signal.Signals(signum).name,
    )


def build_consumer(group: str) -> Consumer:
    return Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap,
            "group.id": group,
            # Cold-start fallback ONLY. Ignored once this group has committed an
            # offset — it is not a per-poll "start from" setting. A brand new
            # group therefore replays the entire retained log, which is exactly
            # how a consumer added next month backfills against old events.
            "auto.offset.reset": "earliest",
            # Manual commit → the ordering below is ours to control. Autocommit
            # fires on a timer regardless of whether the handler finished, which
            # silently degrades at-least-once to at-most-once.
            "enable.auto.commit": False,
        }
    )


def _to_dead_letter(msg: Message, exc: Exception, dlq_topic: str) -> bool:
    """Park an unprocessable message. True only once it is DURABLE.

    Publish, then BLOCK until the broker acks, and only then let the caller
    commit. Committing on an unacked DLQ publish would advance past the message
    with no copy of it anywhere — the one way this design can lose data.
    """
    publish_event(
        dlq_topic,
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


def run_consumer(
    group: str,
    handler: Handler,
    topic: str = Topic.ORDER_DISPATCHED.value,
    dlq_topic: str = Topic.ORDER_DISPATCHED_DLQ.value,
) -> None:
    signal.signal(signal.SIGTERM, _request_stop)
    signal.signal(signal.SIGINT, _request_stop)

    consumer = build_consumer(group)
    consumer.subscribe([topic])
    logger.info(f"Consumer joined '{group}', polling '{topic}'. Ctrl-C to stop.")

    try:
        while _running:
            msg = consumer.poll(timeout=1.0)

            # poll() has a THREE-way return and only one of them is data.
            if msg is None:
                continue
            if msg.error():
                # _PARTITION_EOF is off by default (enable.partition.eof=false),
                # so this sub-branch is defensive; the outer check is not — real
                # errors do arrive here, and .value() on one would crash.
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                logger.error(f"consumer error: {msg.error()}")
                continue

            # --- PROCESS ---
            try:
                payload = json.loads(msg.value().decode("utf-8"))
                handler(payload, msg)
            except Exception as exc:  # noqa: BLE001 — any failure must be caught
                # Without this, an unprocessable message kills the process before
                # the commit and the restart re-reads the SAME message forever:
                # the partition is wedged and every valid event queued behind it
                # is never delivered. Lag monitoring does not show it, because a
                # partition with no committed offset has no lag row at all.
                logger.exception(
                    "unprocessable message → DLQ (partition %s, offset %s)",
                    msg.partition(),
                    msg.offset(),
                )
                if not _to_dead_letter(msg, exc, dlq_topic):
                    logger.critical(
                        "DLQ publish UNCONFIRMED — stopping without committing "
                        "so the message is redelivered, not lost"
                    )
                    break

            # --- COMMIT (only after processing succeeded, or the message was
            # safely parked in the DLQ) ---
            # Placement is the contract: crash between PROCESS and here and the
            # offset never advances, so restart re-reads → at-least-once. Move
            # it ABOVE the handler and a crash in the gap skips the event
            # forever → at-most-once.
            consumer.commit(message=msg)

    finally:
        flush_producer()
        consumer.close()  # clean group leave → immediate rebalance
        logger.info("Consumer closed cleanly.")
