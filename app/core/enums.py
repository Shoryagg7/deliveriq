from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Topic(str, Enum):
    ORDER_DISPATCHED = "order.dispatched"
    ORDER_DELIVERED = "order.delivered"  # Day 33
    # Dead letter: messages the consumer can never process (malformed payload,
    # missing fields). Parked here so a single bad event can't wedge a partition.
    ORDER_DISPATCHED_DLQ = "order.dispatched.dlq"
