"""Day 29 concurrency proof: N simultaneous dispatches across 3 API instances
must produce zero double-assignments (unique order_id AND unique rider_id)."""

from concurrent.futures import ThreadPoolExecutor

import httpx

PORTS = [8000, 8001, 8002]
LAT, LON = 12.9716, 77.5946
N_RIDERS = 10
N_ORDERS = 10
N_DISPATCH = 15  # more calls than orders — losers must fail cleanly, not corrupt


def url(port, path):
    return f"http://localhost:{port}{path}"


def seed():
    riders, orders = [], []
    with httpx.Client(timeout=15) as c:
        for i in range(N_RIDERS):
            r = c.post(url(8000, "/riders"),
                       json={"name": f"race-rider-{i}",
                             "current_lat": LAT, "current_lon": LON})
            r.raise_for_status()
            riders.append(r.json()["id"])
        for i in range(N_ORDERS):
            r = c.post(url(8001, "/orders"),
                       json={"customer_id": 1, "restaurant_id": 1,
                             "value": 100 + i,
                             "pickup_lat": LAT, "pickup_lon": LON,
                             "drop_lat": LAT + 0.01, "drop_lon": LON + 0.01})
            r.raise_for_status()
            orders.append(r.json()["id"])
    return riders, orders


def dispatch(port):
    try:
        r = httpx.post(url(port, "/orders/dispatch"), timeout=30)
        return port, r.status_code, r.json()
    except Exception as e:  # noqa: BLE001
        return port, "ERR", str(e)


def main():
    riders, orders = seed()
    print(f"seeded {len(riders)} riders {riders[0]}..{riders[-1]}, "
          f"{len(orders)} orders {orders[0]}..{orders[-1]}")

    targets = [PORTS[i % 3] for i in range(N_DISPATCH)]
    with ThreadPoolExecutor(max_workers=N_DISPATCH) as ex:
        results = list(ex.map(dispatch, targets))

    ok, failed = [], []
    for port, code, body in results:
        if code == 200:
            ok.append(body["dispatched"])
        else:
            failed.append((port, code, body))

    oids = [d["order_id"] for d in ok]
    rids = [d["rider_id"] for d in ok]
    print(f"\nsuccessful dispatches: {len(ok)}")
    print(f"failed (expected for the {N_DISPATCH - N_ORDERS}+ extra calls): "
          f"{[(p, c, b.get('error') if isinstance(b, dict) else b) for p, c, b in failed]}")
    print(f"assigned pairs: {sorted(zip(oids, rids))}")

    dup_orders = len(oids) != len(set(oids))
    dup_riders = len(rids) != len(set(rids))
    print(f"\nVERDICT  duplicate order_ids: {dup_orders}   "
          f"duplicate rider_ids: {dup_riders}")
    if dup_orders or dup_riders:
        raise SystemExit("❌ DOUBLE-DISPATCH DETECTED")
    print("✅ zero double-assignment across 3 instances")


if __name__ == "__main__":
    main()
