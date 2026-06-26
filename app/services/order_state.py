from app.core.enums import OrderStatus

VALID_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.ASSIGNED, OrderStatus.CANCELLED},
    OrderStatus.ASSIGNED: {OrderStatus.PICKED_UP, OrderStatus.CANCELLED},
    OrderStatus.PICKED_UP: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),  # terminal
    OrderStatus.CANCELLED: set(),  # terminal
}


class InvalidTransition(Exception):
    pass


def transition(current: OrderStatus, target: OrderStatus) -> None:
    if target not in VALID_TRANSITIONS[current]:
        raise InvalidTransition(f"Cannot go from {current.value} to {target.value}")
