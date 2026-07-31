"""Create a login, or promote an existing one, to any role.

/auth/register deliberately always creates a CUSTOMER — an API that lets the
caller declare themselves ops is not an authorization system. Promotion is an
operator action, and this is that action for a single account (seed_users does
the same thing for the three demo logins at once).

    python -m scripts.make_ops me@example.com mypassword123          # -> ops
    python -m scripts.make_ops me@example.com mypassword123 rider    # -> rider
    docker compose exec api python -m scripts.make_ops me@x.com pw12345678

Existing account? The password is left alone and only the role changes, so you
can promote someone who registered through the UI without knowing their password.
"""

import sys

from app.core.database import SessionLocal
from app.core.enums import UserRole
from app.core.security import hash_password
from app.models.rider import Rider
from app.models.user import User


def main() -> None:
    if len(sys.argv) < 3:
        sys.exit(f"usage: python -m {__spec__.name} EMAIL PASSWORD [ROLE]")

    email, password = sys.argv[1], sys.argv[2]
    role_arg = (sys.argv[3] if len(sys.argv) > 3 else "ops").lower()

    valid = {r.value for r in UserRole}
    if role_arg not in valid:
        sys.exit(f"role must be one of {sorted(valid)}, got {role_arg!r}")

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            user = User(email=email, hashed_password=hash_password(password))
            db.add(user)
            action = "created"
        else:
            # Deliberately NOT resetting the password: promoting an account you
            # do not own should not also let you take it over.
            action = "promoted"

        user.role = role_arg

        if role_arg == UserRole.RIDER.value and user.rider_id is None:
            # A rider login without a Rider row cannot pass the ownership check,
            # which compares order.rider_id against user.rider_id.
            rider = Rider(name=f"{email.split('@')[0]}-rider",
                          current_lat=28.6105, current_lon=77.2005)
            db.add(rider)
            db.flush()
            user.rider_id = rider.id
            # Postgres row is only half of onboarding — matching reads Redis.
            from app.services.geohash_service import add_rider

            add_rider(rider.id, rider.current_lat, rider.current_lon)

        db.commit()
        link = f" -> rider {user.rider_id}" if user.rider_id else ""
        print(f"  {action}: {email}  role={user.role}{link}")
        if action == "promoted":
            print("  (password unchanged)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
