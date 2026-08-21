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
from app.models.user import User
from app.services.dispatch import pick_next_order
from app.services.geohash_service import add_rider, update_rider_location

PICKUP = (28.6100, 77.2000)
DROP = (28.6500, 77.2500)
JITTER = 0.0015  # ~165m — comfortably inside the geohash search ring

DEMO_CUSTOMER = "customer@deliveriq.io"  # created by scripts.seed_users
DEMO_RIDER_LOGIN = "rider@deliveriq.io"  # ditto — must end up holding an order

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

        # Orders belong to a REAL user now (G02): customer_id is derived from
        # the token at the API, and order listings are scoped by owner — a
        # random id would seed orders no demo login can see.
        customer = db.query(User).filter(User.email == DEMO_CUSTOMER).first()
        if customer is None:
            raise SystemExit(
                f"no {DEMO_CUSTOMER} user — run `python -m scripts.seed_users` first"
            )

        for _ in range(N_ORDERS):
            db.add(
                Order(
                    customer_id=customer.id,
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

        # The rider LOGIN has to end up holding an order, or signing in as
        # `rider` shows an empty board and the whole role demo falls flat.
        # Previously this was luck: Demo Rider sits ~70 m from the pickup while
        # the couriers are jittered 0-165 m, so on some runs four dispatches all
        # went to couriers.
        #
        # Park the demo rider exactly ON the pickup point instead. On the first
        # dispatch every rider has 0 orders today, so the fairness band falls
        # through to distance — and 0 m wins. No special-casing inside dispatch;
        # the demo rider simply wins the real algorithm, deterministically.
        demo_rider = (
            db.query(Rider)
            .join(User, User.rider_id == Rider.id)
            .filter(User.email == DEMO_RIDER_LOGIN)
            .first()
        )
        if demo_rider is not None:
            demo_rider.current_lat, demo_rider.current_lon = PICKUP
            db.commit()
            update_rider_location(demo_rider.id, PICKUP[0], PICKUP[1])

        assigned = 0
        for _ in range(N_DISPATCH):
            try:
                pick_next_order(db)
                assigned += 1
            except Exception as exc:  # noqa: BLE001 — report and stop, don't crash
                print(f"  dispatch stopped early: {type(exc).__name__}")
                break
        print(f"  {assigned} dispatched, {N_ORDERS - assigned} left PENDING")

        if demo_rider is not None:
            mine = db.query(Order).filter(Order.rider_id == demo_rider.id).count()
            note = "" if mine else "  <- NOT OK, rider login has nothing to advance"
            print(f"  {DEMO_RIDER_LOGIN} holds {mine} order(s){note}")
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
