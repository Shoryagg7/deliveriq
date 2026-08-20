"""Load profile for DeliverIQ.

Rewritten for G10. The old file had a single task hitting UNAUTHENTICATED
`POST /orders`, so the headline "~123 RPS, p99 220 ms" measured a plain INSERT —
no auth, no matching, no row locks, no Kafka. The number was real and the claim
attached to it was not.

This drives the path anyone actually cares about: the dispatch CLAIM, under
contention, with a seeded rider fleet. Run it against three replicas so the
SKIP LOCKED protocol is genuinely contended rather than simulated:

    API_PORTS=8000-8002:8000 docker compose up -d --scale api=3
    python -m scripts.seed_users
    RATE_LIMIT_ENABLED=false locust -f locustfile.py --host http://localhost:8000

Report dispatch throughput and the p99 of `POST /orders/dispatch` separately
from order creation — they are different systems wearing one API.
"""

import os
import random

from locust import HttpUser, between, task

OPS_EMAIL = os.getenv("LOAD_OPS_EMAIL", "ops@deliveriq.io")
OPS_PASSWORD = os.getenv("LOAD_OPS_PASSWORD", "opspassword123")

PICKUP_LAT, PICKUP_LON = 12.9716, 77.5946


class DispatchUser(HttpUser):
    """Authenticates once, then mixes order creation with dispatch claims."""

    wait_time = between(0.1, 0.5)

    def on_start(self):
        r = self.client.post(
            "/auth/login",
            json={"email": OPS_EMAIL, "password": OPS_PASSWORD},
            name="/auth/login",
        )
        if r.status_code != 200:
            raise RuntimeError(
                f"login failed for {OPS_EMAIL} ({r.status_code}). "
                "Run: python -m scripts.seed_users"
            )
        self.client.headers["Authorization"] = f"Bearer {r.json()['access_token']}"

    @task(3)
    def create_order(self):
        """Supply side. Keeps the pending queue non-empty so dispatch has work."""
        self.client.post(
            "/orders",
            json={
                # No customer_id — it comes from the token (G02).
                "restaurant_id": random.randint(1, 100),
                "value": random.randint(100, 1000),
                "pickup_lat": PICKUP_LAT + random.uniform(-0.002, 0.002),
                "pickup_lon": PICKUP_LON + random.uniform(-0.002, 0.002),
                "drop_lat": PICKUP_LAT + 0.01,
                "drop_lon": PICKUP_LON + 0.01,
            },
            name="/orders [create]",
        )

    @task(1)
    def dispatch(self):
        """THE measurement. 409 means no rider was free — a real outcome under
        load, not an error, so it must not be recorded as a failure or the run
        reports a fake error rate."""
        with self.client.post(
            "/orders/dispatch", name="/orders/dispatch [claim]", catch_response=True
        ) as r:
            if r.status_code in (200, 404, 409):
                r.success()
            else:
                r.failure(f"unexpected {r.status_code}")
