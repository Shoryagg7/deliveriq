"""Rebuild the Redis geohash index from Postgres.

The index is a DERIVED view of rider locations, but until now it was only ever
written forward — POST /riders adds a rider, dispatch removes one. Nothing could
rebuild it, so any event that emptied Redis (a `down -v`, an eviction, a restart
without persistence) left every AVAILABLE rider in Postgres invisible to
matching, with no error anywhere. Postgres would say 40 riders free and dispatch
would answer "no rider available nearby".

Derived state must be reconstructible from the source of truth. This is that
reconstruction:

    python -m scripts.reindex_riders
    docker compose exec api python -m scripts.reindex_riders
"""

from app.core.database import SessionLocal
from app.core.redis_client import redis_client
from app.models.rider import Rider
from app.services.geohash_service import add_rider, remove_rider_from_index


def main() -> None:
    db = SessionLocal()
    try:
        riders = db.query(Rider).all()
        indexed = skipped = 0
        for rider in riders:
            if rider.status == "AVAILABLE":
                # add_rider is idempotent (SADD + HSET), so re-running is safe.
                add_rider(rider.id, rider.current_lat, rider.current_lon)
                indexed += 1
            else:
                # A BUSY rider must NOT be selectable. Clearing explicitly means
                # a stale entry from before a crash cannot resurrect them.
                remove_rider_from_index(rider.id)
                skipped += 1
    finally:
        db.close()

    print(f"  {indexed} AVAILABLE riders indexed")
    print(f"  {skipped} BUSY riders excluded")
    cells = len(redis_client.keys("geohash:*"))
    print(f"  {cells} geohash cells populated")


if __name__ == "__main__":
    main()
