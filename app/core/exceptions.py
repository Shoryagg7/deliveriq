class DeliverIQError(Exception):
    """Base for all app errors."""

    status_code = 500
    code = "INTERNAL_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class OrderNotFound(DeliverIQError):
    status_code = 404
    code = "ORDER_NOT_FOUND"


class RiderNotFound(DeliverIQError):
    status_code = 404
    code = "RIDER_NOT_FOUND"


class NoPendingOrders(DeliverIQError):
    status_code = 404
    code = "NO_PENDING_ORDERS"


class RiderUnavailable(DeliverIQError):
    status_code = 409
    code = "RIDER_UNAVAILABLE"


class InvalidTransition(DeliverIQError):
    status_code = 400
    code = "INVALID_TRANSITION"
