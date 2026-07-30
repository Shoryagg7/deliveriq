# app/models/dispatch_event.py
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, UniqueConstraint

from app.core.database import Base


class DispatchEvent(Base):
    """What the `analytics` consumer group writes — one row per event CONSUMED.

    At-least-once means the SAME message is redelivered after a crash between
    processing and commit. (partition, offset) uniquely identifies a message in
    Kafka, so a unique constraint on that pair turns redelivery into a no-op:
    the consumer stays at-least-once, the effect becomes exactly-once. That is
    what "effectively-once" means — you don't get it from a broker setting, you
    get it by making the write idempotent.

    Note the limit: this dedupes redelivery of one message. It does NOT dedupe
    the same real-world fact PUBLISHED twice (a producer retry creating a second
    message at a different offset) — that needs an event_id inside the payload.
    Different problem, different key.
    """

    __tablename__ = "dispatch_events"
    __table_args__ = (
        UniqueConstraint("kafka_partition", "kafka_offset", name="uq_dispatch_event_msg"),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    rider_id = Column(Integer, nullable=False)
    dispatched_at = Column(DateTime, nullable=False)  # producer's ts
    recorded_at = Column(DateTime, default=lambda: datetime.now(UTC))
    # "offset" is a reserved word in Postgres — prefix rather than fight quoting
    kafka_partition = Column(Integer, nullable=False)
    kafka_offset = Column(Integer, nullable=False)
