# # ─────────────────────────────────────────────
# # PART 1: Functions with type hints
# # ─────────────────────────────────────────────

# def calculate_priority(order_value: float, wait_minutes: int) -> float:
#     """
#     Higher score = more urgent = dispatched first.
#     This exact formula will power your priority queue on Day 17.
#     """
#     return order_value * 0.4 + wait_minutes * 0.6

# # Test it
# print(calculate_priority(500, 15))   # → 209.0
# print(calculate_priority(1000, 0))   # → 400.0
# print(calculate_priority(100, 60))   # → 76.0  (cheap but been waiting!)


# # ─────────────────────────────────────────────
# # PART 2: Classes (this IS your Day 11 DB model, just without SQLAlchemy yet)
# # ─────────────────────────────────────────────

# class Rider:
#     def __init__(self, rider_id: int, name: str, lat: float, lon: float):
#         self.rider_id = rider_id
#         self.name = name
#         self.lat = lat
#         self.lon = lon
#         self.is_available = True
#         self.current_order_id = None   # None = Python's nullptr

#     def assign_order(self, order_id: int) -> bool:
#         """Returns True if assignment succeeded, False if rider already busy."""
#         if not self.is_available:
#             print(f"❌ Rider {self.name} is busy with order {self.current_order_id}")
#             return False
#         self.is_available = False
#         self.current_order_id = order_id
#         print(f"✅ Rider {self.name} assigned to order {order_id}")
#         return True

#     def complete_order(self):
#         """Mark rider as free after delivery."""
#         print(f"🏁 Rider {self.name} completed order {self.current_order_id}")
#         self.is_available = True
#         self.current_order_id = None

#     def __repr__(self) -> str:
#         """This is like operator<< in C++ — controls how the object prints."""
#         status = "available" if self.is_available else f"busy({self.current_order_id})"
#         return f"Rider(id={self.rider_id}, name={self.name}, status={status})"


# # Test the class
# r1 = Rider(1, "Suresh", 28.61, 77.20)
# r2 = Rider(2, "Ramesh", 28.63, 77.22)
# r3 = Rider(3, "Ritu", 28.65, 77.25)


# r1.assign_order(101)
# r1.assign_order(102)   # should fail — already busy
# r2.assign_order(102)   # should succeed
# r1.complete_order()
# r1.assign_order(103)   # now succeeds again

# print()
# print(r1)
# print(r2)


# # ─────────────────────────────────────────────
# # PART 3: Exception handling (you'll use this in FastAPI on Day 12)
# # ─────────────────────────────────────────────

# class RiderUnavailableError(Exception):
#     """Custom exception — same concept as std::exception subclass in C++."""
#     pass

# def assign_or_raise(rider: Rider, order_id: int):
#     """Raises an exception instead of returning False. Cleaner for APIs."""
#     if not rider.is_available:
#         raise RiderUnavailableError(
#             f"Rider {rider.rider_id} is already assigned to order {rider.current_order_id}"
#         )
#     rider.assign_order(order_id)

# # Test exceptions
# try:
#     assign_or_raise(r2, 999)   # r2 is busy — should raise
# except RiderUnavailableError as e:
#     print(f"Caught exception: {e}")

# try:
#     assign_or_raise(r3, 999)   # r3 is free — should succeed
# except RiderUnavailableError as e:
#     print(f"Caught exception: {e}")


class Rider:
    def __init__(self, rider_id: int, name: str, lat: float, lon: float):
        self.rider_id = rider_id
        self.name = name
        self.lat = lat
        self.lon = lon

        self.is_available = True
        self.current_order_id = None

        self.rating = 5.0  # Default displayed rating
        self.rating_count = 0  # No actual ratings yet

        self.completed_orders = []

    def assign_order(self, order_id: int) -> bool:
        """Assign an order if the rider is available."""
        if not self.is_available:
            print(f"❌ Rider {self.name} is busy with order {self.current_order_id}")
            return False

        self.is_available = False
        self.current_order_id = order_id

        print(f"✅ Rider {self.name} assigned to order {order_id}")
        return True

    def complete_order(self):
        """Mark the current order as completed."""
        if self.current_order_id is None:
            print(f"⚠️ Rider {self.name} has no active order.")
            return
        print(f"🏁 Rider {self.name} completed order {self.current_order_id}")

        self.completed_orders.append(self.current_order_id)

        self.is_available = True
        self.current_order_id = None


    def rate_rider(self, score: float):
        if not (1.0 <= score <= 5.0):
            raise ValueError("Rating must be between 1.0 and 5.0")
        self.rating = (self.rating * self.rating_count + score) / (self.rating_count + 1)
        self.rating_count += 1
        print(f"⭐ Rider {self.name} rating updated to {self.rating:.2f} ({self.rating_count} ratings)")

    def total_deliveries(self) -> int:
        return len(self.completed_orders)

    def __repr__(self) -> str:
        status = (
            "available" if self.is_available else f"busy(order={self.current_order_id})"
        )

        return (
            f"Rider(id={self.rider_id}, "
            f"name='{self.name}', "
            f"rating={self.rating:.2f}, "
            f"deliveries={self.total_deliveries()}, "
            f"status={status})"
        )


class Order:
    def __init__(
        self,
        order_id: int,
        customer_id: int,
        value: float,
        status: str = "PENDING",
    ):
        self.order_id = order_id
        self.customer_id = customer_id
        self.value = value
        self.status = status

    def cancel(self):
        if self.status == "DELIVERED":
            raise ValueError(f"Cannot cancel order {self.order_id}: already delivered.")
        if self.status == "CANCELLED":
            raise ValueError(f"Order {self.order_id} is already cancelled.")
        self.status = "CANCELLED"
        print(f"❌ Order {self.order_id} cancelled.")

    def __repr__(self) -> str:
        return (
            f"Order(order_id={self.order_id}, "
            f"customer_id={self.customer_id}, "
            f"value={self.value}, "
            f"status='{self.status}')"
        )

if __name__ == "__main__":
    # Test Rider
    r = Rider(1, "Suresh", 28.61, 77.20)
    r.assign_order(101)
    r.complete_order()
    r.assign_order(102)
    r.complete_order()

    r.rate_rider(4.0)
    r.rate_rider(5.0)
    r.rate_rider(3.0)

    try:
        r.rate_rider(6.0)  # should raise
    except ValueError as e:
        print(f"Caught: {e}")

    print(r)
    print(f"Total deliveries: {r.total_deliveries()}")
    print(f"Completed orders: {r.completed_orders}")

    # Test Order
    o1 = Order(1, 101, 500.0)
    o1.cancel()
    print(o1)

    o2 = Order(2, 102, 800.0, status="DELIVERED")
    try:
        o2.cancel()  # should raise
    except ValueError as e:
        print(f"Caught: {e}")
