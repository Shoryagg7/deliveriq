# app/core/kafka_producer.py
import json
import logging

from confluent_kafka import Producer

from app.core.config import settings

logger = logging.getLogger("deliveriq")

_producer: Producer | None = None


def get_producer() -> Producer:
    """One Producer per process. Created lazily on first use."""
    global _producer
    if _producer is None:
        _producer = Producer(
            {
                "bootstrap.servers": settings.kafka_bootstrap,
                "acks": "all",
                "enable.idempotence": True,
                "client.id": "deliveriq-api",
                # librdkafka defaults to CRC32; the Java client uses murmur2.
                # Same key -> different partition across clients -> per-key
                # ordering silently breaks. Pin to the ecosystem default.
                "partitioner": "murmur2_random",
            }
        )
        logger.info("kafka producer created bootstrap=%s", settings.kafka_bootstrap)
    return _producer


def _delivery_report(err, msg) -> None:
    """Called by librdkafka's background thread once the broker acks (or gives up)."""
    if err is not None:
        logger.error("kafka delivery FAILED topic=%s err=%s", msg.topic(), err)
    else:
        logger.info(
            "kafka delivered topic=%s partition=%s offset=%s",
            msg.topic(),
            msg.partition(),
            msg.offset(),
        )


def publish_event(topic: str, payload: dict, key: str | None = None) -> None:
    """Enqueue an event. Returns immediately — delivery happens in the background."""
    producer = get_producer()
    producer.produce(
        topic,
        key=key.encode() if key else None,
        value=json.dumps(payload).encode(),
        callback=_delivery_report,
    )
    producer.poll(0)  # serve delivery callbacks; does NOT block


def flush_producer(timeout: float = 5.0) -> None:
    """Block until the local queue drains. Shutdown only."""
    if _producer is None:
        return
    remaining = _producer.flush(timeout)
    if remaining:
        logger.error("kafka flush timed out — %d messages UNDELIVERED", remaining)
