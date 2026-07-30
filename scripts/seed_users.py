"""Create one demo login per role, idempotently.

Roles cannot be self-assigned through /auth/register — that endpoint always
creates a CUSTOMER, deliberately, since an API that lets a caller declare
themselves ops is not an authorization system. Promotion is an operator action,
which is what this script is.

    python -m scripts.seed_users            # against .env DATABASE_URL
    docker compose exec api python -m scripts.seed_users

    ops@deliveriq.io      / opspassword123      full access, sees /admin/stats
    rider@deliveriq.io    / riderpassword123    may advance ITS OWN orders
    customer@deliveriq.io / custpassword123     may not touch status at all
"""

from app.core.database import SessionLocal
from app.core.enums import UserRole
from app.core.security import hash_password
from app.models.rider import Rider
from app.models.user import User
from app.services.geohash_service import add_rider

DEMO_USERS = [
    ("ops@deliveriq.io", "opspassword123", UserRole.OPS, False),
    ("rider@deliveriq.io", "riderpassword123", UserRole.RIDER, True),
    ("customer@deliveriq.io", "custpassword123", UserRole.CUSTOMER, False),
]


def main() -> None:
    db = SessionLocal()
    try:
        for email, password, role, needs_rider in DEMO_USERS:
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                user = User(email=email, hashed_password=hash_password(password))
                db.add(user)
            # Re-applied every run so a role edited by hand snaps back, and so
            # re-running after `down -v` is safe.
            user.role = role.value

            if needs_rider:
                # A rider login is meaningless without a Rider row to act as —
                # the ownership check compares order.rider_id to user.rider_id.
                rider = db.query(Rider).filter(Rider.name == "Demo Rider").first()
                if rider is None:
                    rider = Rider(
                        name="Demo Rider", current_lat=28.6105, current_lon=77.2005
                    )
                    db.add(rider)
                    db.flush()  # need the id before linking
                user.rider_id = rider.id
                # Writing the row is only HALF of onboarding a rider. Matching
                # reads the Redis geohash index, not the table, so a rider
                # created straight through SQLAlchemy is AVAILABLE in Postgres
                # and invisible to dispatch. POST /riders calls this; a script
                # that bypasses the endpoint has to call it too.
                add_rider(rider.id, rider.current_lat, rider.current_lon)

            db.commit()
            link = f" -> rider {user.rider_id}" if user.rider_id else ""
            print(f"  {email:24} {role.value:9} {password}{link}")
    finally:
        db.close()

    print("\nSign in at http://localhost:8000 with any of the above.")


if __name__ == "__main__":
    main()
