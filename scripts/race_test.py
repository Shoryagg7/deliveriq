"""Concurrency proof: N simultaneous dispatches across 3 API replicas must
produce zero double-assignments (unique order_id AND unique rider_id).

Every replica runs the same code against the same Postgres, so the only thing
stopping two of them handing the same rider to two different orders is the
`SELECT ... FOR UPDATE SKIP LOCKED` claim. This script tries to break that.

    API_PORTS=8000-8002:8000 docker compose up -d --scale api=3
    python -m scripts.race_test

Dispatch is an ops action, so the script authenticates first. Run seed_users
(or make_ops) beforehand, or pass credentials:

    python -m scripts.race_test ops@deliveriq.io opspassword123
"""

import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

import httpx

PORTS = [8000, 8001, 8002]
LAT, LON = 12.9716, 77.5946
N_RIDERS = 10
N_ORDERS = 10
N_DISPATCH = 15  # more calls than orders — losers must fail cleanly, not corrupt

EMAIL = sys.argv[1] if len(sys.argv) > 1 else "ops@deliveriq.io"
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else "opspassword123"


def url(port, path):
    return f"http://localhost:{port}{path}"


def login() -> dict[str, str]:
    """Dispatch and rider onboarding are ops-only; without this every call 401s."""
    try:
        r = httpx.post(url(8000, "/auth/login"),
                       json={"email": EMAIL, "password": PASSWORD}, timeout=15)
    except httpx.ConnectError:
        sys.exit("no API on :8000 — is the stack up?")
    if r.status_code != 200:
        sys.exit(f"login failed for {EMAIL} ({r.status_code}). "
                 f"Run: python -m scripts.seed_users")
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def check_replicas() -> None:
    """A 'concurrency test' against one replica three times proves nothing."""
    live = []
    for p in PORTS:
        try:
            if httpx.get(url(p, "/health"), timeout=5).status_code == 200:
                live.append(p)
        except httpx.HTTPError:
            pass
    if len(live) < 2:
        sys.exit(f"only {live} responding — scale up first:\n"
                 f"  API_PORTS=8000-8002:8000 docker compose up -d --scale api=3")
    print(f"replicas live on {live}")


def seed(headers):
    riders, orders = [], []
    with httpx.Client(timeout=15) as c:
        for i in range(N_RIDERS):
            r = c.post(url(8000, "/riders"), headers=headers,
                       json={"name": f"race-rider-{i}",
                             "current_lat": LAT, "current_lon": LON})
            r.raise_for_status()
            riders.append(r.json()["id"])
        for i in range(N_ORDERS):
            # Authenticated like everything else now (G02): customer_id comes
            # from the token, so it is no longer a field to send.
            r = c.post(url(8001, "/orders"), headers=headers,
                       json={"restaurant_id": 1,
                             "value": 100 + i,
                             "pickup_lat": LAT, "pickup_lon": LON,
                             "drop_lat": LAT + 0.01, "drop_lon": LON + 0.01})
            r.raise_for_status()
            orders.append(r.json()["id"])
    return riders, orders


def dispatch(args):
    port, headers = args
    try:
        r = httpx.post(url(port, "/orders/dispatch"), headers=headers, timeout=30)
        return port, r.status_code, r.json()
    except Exception as e:  # noqa: BLE001
        return port, "ERR", str(e)


def main():
    check_replicas()
    headers = login()
    print(f"authenticated as {EMAIL}")

    riders, orders = seed(headers)
    print(f"seeded {len(riders)} riders {riders[0]}..{riders[-1]}, "
          f"{len(orders)} orders {orders[0]}..{orders[-1]}")

    targets = [(PORTS[i % 3], headers) for i in range(N_DISPATCH)]
    print(f"firing {N_DISPATCH} simultaneous dispatches across {len(PORTS)} replicas...")
    with ThreadPoolExecutor(max_workers=N_DISPATCH) as ex:
        results = list(ex.map(dispatch, targets))

    ok, failed = [], []
    for port, code, body in results:
        if code == 200:
            ok.append((port, body["dispatched"]))
        else:
            failed.append((port, code, body))

    by_port = Counter(p for p, _ in ok)
    oids = [d["order_id"] for _, d in ok]
    rids = [d["rider_id"] for _, d in ok]

    print(f"\nsuccessful dispatches: {len(ok)}   per replica: {dict(sorted(by_port.items()))}")
    print(f"failed (expected for the {N_DISPATCH - N_ORDERS}+ extra calls): "
          f"{[(p, c, b.get('error') if isinstance(b, dict) else b) for p, c, b in failed]}")
    print(f"assigned pairs: {sorted(zip(oids, rids, strict=True))}")

    dup_orders = len(oids) != len(set(oids))
    dup_riders = len(rids) != len(set(rids))
    print(f"\nVERDICT  duplicate order_ids: {dup_orders}   "
          f"duplicate rider_ids: {dup_riders}")
    if dup_orders or dup_riders:
        raise SystemExit("❌ DOUBLE-DISPATCH DETECTED")
    print("✅ zero double-assignment across replicas")


if __name__ == "__main__":
    main()
