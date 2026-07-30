"""Put the system into a good state for a live demo.

Run after a fresh `docker compose up`, or any time the data gets messy:

    python -m scripts.seed_users     # logins first — seed_demo needs the rider
    python -m scripts.seed_demo

Leaves: riders idle near the pickup point, a few orders already ASSIGNED so the
board isn't empty, and several still PENDING so "Dispatch next" has something to
do while someone is watching.

Rider positions are jittered by only ~165m on purpose. Geohash precision is 6
(~1.2km x 0.61km cells) and matching searches the order's cell plus its eight
neighbours, so a rider more than one cell away is invisible to dispatch even
while AVAILABLE — the failure this seeder exists to avoid reproducing.
"""

import random

from app.core.database import SessionLocal
from app.core.kafka_producer import flush_producer
from app.models.order import Order
from app.models.rider import Rider
from app.services.dispatch import pick_next_order
from app.services.geohash_service import add_rider

PICKUP = (28.6100, 77.2000)
DROP = (28.6500, 77.2500)
JITTER = 0.0015  # ~165m — comfortably inside the geohash search ring

N_RIDERS = 6
N_ORDERS = 9
N_DISPATCH = 4  # leaves N_ORDERS - N_DISPATCH pending for the live demo


def main() -> None:
    random.seed()
    db = SessionLocal()
    try:
        riders = []
        for i in range(N_RIDERS):
            rider = Rider(
                name=f"Courier {i + 1}",
                current_lat=PICKUP[0] + (random.random() - 0.5) * JITTER * 2,
                current_lon=PICKUP[1] + (random.random() - 0.5) * JITTER * 2,
            )
            db.add(rider)
            db.flush()
            # Writing the row is half the job — matching reads the Redis index.
            add_rider(rider.id, rider.current_lat, rider.current_lon)
            riders.append(rider)

        for _ in range(N_ORDERS):
            db.add(
                Order(
                    customer_id=random.randint(1, 200),
                    restaurant_id=random.randint(1, 30),
                    value=random.randint(120, 950),
                    pickup_lat=PICKUP[0],
                    pickup_lon=PICKUP[1],
                    drop_lat=DROP[0],
                    drop_lon=DROP[1],
                )
            )
        db.commit()
        print(f"  {N_RIDERS} riders (indexed), {N_ORDERS} orders created")

        assigned = 0
        for _ in range(N_DISPATCH):
            try:
                pick_next_order(db)
                assigned += 1
            except Exception as exc:  # noqa: BLE001 — report and stop, don't crash
                print(f"  dispatch stopped early: {type(exc).__name__}")
                break
        print(f"  {assigned} dispatched, {N_ORDERS - assigned} left PENDING")
    finally:
        db.close()

    # produce() only ENQUEUES — it does no I/O and cannot fail on a dead broker.
    # A short-lived script that exits here loses every buffered event, so the
    # three consumer groups would see nothing and the demo would look broken.
    # This is the same dual-write hole the API closes with flush-on-shutdown.
    undelivered = flush_producer(10.0)
    if undelivered:
        print(f"  WARNING: {undelivered} events never reached Kafka")
    else:
        print("  all dispatch events flushed to Kafka")

    print("\n  http://localhost:8000        console (sign in as ops)")
    print("  http://localhost:3000        Grafana")
    print("  http://localhost:8080        Kafka UI")


if __name__ == "__main__":
    main()
