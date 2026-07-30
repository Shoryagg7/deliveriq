# app/models/dispatch_event.py
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer

from app.core.database import Base


class DispatchEvent(Base):
    """What the `analytics` consumer group writes — one row per event CONSUMED.

    Deliberately NOT deduplicated yet. Delivery is at-least-once, so a crash
    before commit (or a group whose offsets are reset) replays events and this
    table double-counts. Storing kafka_partition/kafka_offset makes those
    duplicates visible rather than mysterious, and gives Day 34 a natural
    dedupe key to build on.
    """

    __tablename__ = "dispatch_events"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False, index=True)
    rider_id = Column(Integer, nullable=False)
    dispatched_at = Column(DateTime, nullable=False)  # producer's ts
    recorded_at = Column(DateTime, default=lambda: datetime.now(UTC))
    # "offset" is a reserved word in Postgres — prefix rather than fight quoting
    kafka_partition = Column(Integer, nullable=False)
    kafka_offset = Column(Integer, nullable=False)
