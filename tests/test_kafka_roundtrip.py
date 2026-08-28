"""One test that uses a REAL broker.

Everything else patches `publish_event` at its call sites, which is right for
speed and isolation — but it means no test proves an event survives an actual
broker. The suite could stay green while serialisation, the partitioner, or the
topic config was broken.

This closes that: produce for real, consume for real, assert the payload and the
partitioning both survived. Marked `real_kafka` so it opts out of the autouse
mock (see conftest).
"""

import json
import uuid

import pytest
from confluent_kafka import Consumer

from app.core.config import settings
from app.core.kafka_producer import flush_producer, publish_event

TOPIC = "test.roundtrip"
POLL_TIMEOUT = 30.0


@pytest.mark.real_kafka
def test_event_round_trips_a_real_broker():
    key = uuid.uuid4().hex
    sent = {"order_id": 4242, "rider_id": 7, "marker": key}

    publish_event(TOPIC, sent, key=key)
    # flush returns messages STILL undelivered — 0 means the broker acked.
    assert flush_producer(20.0) == 0, "broker never acknowledged the publish"

    consumer = Consumer(
        {
            "bootstrap.servers": settings.kafka_bootstrap,
            # Fresh group every run, so this test never inherits a committed
            # offset from a previous one and skip its own message.
            "group.id": f"roundtrip-{uuid.uuid4().hex}",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    consumer.subscribe([TOPIC])
    try:
        deadline = POLL_TIMEOUT
        received = None
        while deadline > 0 and received is None:
            msg = consumer.poll(timeout=1.0)
            deadline -= 1.0
            if msg is None or msg.error():
                continue
            payload = json.loads(msg.value().decode())
            if payload.get("marker") == key:      # ignore other runs' messages
                received = (payload, msg)
    finally:
        consumer.close()

    assert received is not None, f"no message with marker {key} within {POLL_TIMEOUT}s"
    payload, msg = received
    assert payload == sent, "payload did not survive the round trip"
    assert msg.key().decode() == key, "partition key did not survive"
