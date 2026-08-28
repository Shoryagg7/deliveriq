# app/models/outbox.py
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Index, Integer, String, Text

from app.core.database import Base


class OutboxEvent(Base):
    """One event, written inside the SAME transaction as the state it describes.

    This closes the dual-write hole. Previously dispatch committed the order and
    then published to Kafka — two systems, no shared transaction — so a crash in
    the gap left the order assigned and the event gone forever.

    Now the event is a row. It commits atomically with the order and the rider,
    and a separate relay publishes it afterwards. The relay may publish the same
    row twice if it dies between publishing and marking; that is at-least-once,
    which the consumers already dedupe on `(partition, offset)`.

    The trade is honest: the event is no longer lost, but it is no longer
    instant either — it is delayed by the relay's poll interval.
    """

    __tablename__ = "outbox"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    # Kafka partition key. Same key -> same partition -> per-key ordering.
    key = Column(String, nullable=True)
    payload = Column(Text, nullable=False)  # JSON, serialised at write time
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    # NULL until the broker has acked it. This column IS the queue.
    published_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        # Partial index: the relay only ever asks for unpublished rows, so
        # indexing the published ones would grow forever for no reader.
        Index(
            "ix_outbox_unpublished",
            "created_at",
            postgresql_where=published_at.is_(None),
        ),
    )
