# app/models/order.py
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String

from app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    # FK, not a bare integer: the handler already derives this from the verified
    # token, but application-level invariants are bypassed by scripts, fixtures
    # and the next endpoint someone adds. RESTRICT so deleting a customer fails
    # loudly instead of silently vaporising their order history.
    customer_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    restaurant_id = Column(Integer, nullable=False)
    value = Column(Float, nullable=False)
    pickup_lat = Column(Float, nullable=False)
    pickup_lon = Column(Float, nullable=False)
    drop_lat = Column(Float, nullable=False)
    drop_lon = Column(Float, nullable=False)
    status = Column(String, default="PENDING", index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    rider_id = Column(Integer, ForeignKey("riders.id"), nullable=True)
