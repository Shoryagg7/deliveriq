import math
import time
from datetime import UTC, datetime

import geohash

from app.core.redis_client import redis_client

PRECISION = 6  # ~1.2 km cells


def _orders_key(rider_id: int) -> str:
    today = datetime.now(UTC).strftime("%Y-%m-%d")
    return f"rider:{rider_id}:orders:{today}"

def add_rider(rider_id: int, lat: float, lon: float):
    cell = geohash.encode(lat, lon, PRECISION)
    redis_client.sadd(f"geohash:{cell}", rider_id)
    redis_client.hset(
        f"rider:{rider_id}:loc", mapping={"lat": lat, "lon": lon, "cell": cell}
    )


def find_nearby_riders(lat: float, lon: float) -> list[int]:
    cell = geohash.encode(lat, lon, PRECISION)
    cells_to_check = [cell] + geohash.neighbors(cell)  # home + 8 neighbours
    riders = set()
    for c in cells_to_check:
        riders.update(redis_client.smembers(f"geohash:{c}"))
    return [int(r) for r in riders]


def _haversine(lat1, lon1, lat2, lon2) -> float:
    R = 6_371_000  # earth radius, metres
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def select_rider(order_lat: float, order_lon: float, band_m: float = 500) -> int | None:
    candidates = find_nearby_riders(order_lat, order_lon)
    if not candidates:
        return None

    scored = []
    for rid in candidates:
        loc = redis_client.hgetall(f"rider:{rid}:loc")
        if not loc:
            continue
        dist = _haversine(order_lat, order_lon, float(loc["lat"]), float(loc["lon"]))
        orders_today = int(redis_client.get(_orders_key(rid)) or 0)
        scored.append((rid, dist, orders_today))
    if not scored:
        return None

    d_min = min(s[1] for s in scored)
    feasible = [s for s in scored if s[1] <= d_min + band_m]  # within band of nearest
    feasible.sort(key=lambda s: (s[2], s[1]))  # fewest orders, then nearest
    chosen = feasible[0][0]

    redis_client.hset(f"rider:{chosen}", "last_assigned_at", int(time.time()))
    key = _orders_key(chosen)
    redis_client.incr(key)
    redis_client.expire(key, 172800)   # 48h TTL — auto-cleans old days
    return chosen

def update_rider_location(rider_id: int, lat: float, lon: float):
    old_cell = redis_client.hget(f"rider:{rider_id}:loc", "cell")
    new_cell = geohash.encode(lat, lon, PRECISION)
    if old_cell and old_cell != new_cell:
        redis_client.srem(f"geohash:{old_cell}", rider_id)  # leave stale cell
    redis_client.sadd(f"geohash:{new_cell}", rider_id)
    redis_client.hset(
        f"rider:{rider_id}:loc", mapping={"lat": lat, "lon": lon, "cell": new_cell}
    )

def remove_rider_from_index(rider_id: int):
    cell = redis_client.hget(f"rider:{rider_id}:loc", "cell")
    if cell:
        redis_client.srem(f"geohash:{cell}", rider_id)
