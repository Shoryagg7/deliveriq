"""Auth dependencies — who is calling, and may they."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.enums import OrderStatus, UserRole
from app.core.revocation import is_revoked
from app.core.security import decode_access_token
from app.models.user import User

# auto_error=False so a missing header produces our 401 envelope rather than
# FastAPI's default shape — one error contract across the whole API.
_bearer = HTTPBearer(auto_error=False)

_UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise _UNAUTHENTICATED

    claims = decode_access_token(creds.credentials)
    if claims is None or not claims.get("sub"):
        raise _UNAUTHENTICATED

    # A valid signature is not the same as a live session: logout puts this
    # token's jti on a denylist that outlives it by exactly its remaining life.
    if is_revoked(claims.get("jti")):
        raise _UNAUTHENTICATED

    # Load the user rather than trusting the token's claims wholesale: a token
    # stays valid until it expires, so a user deleted or demoted a minute ago
    # would otherwise keep full access for the rest of the token's life.
    user = db.query(User).filter(User.email == claims["sub"]).first()
    if user is None:
        raise _UNAUTHENTICATED
    return user


def require_ops(user: User = Depends(get_current_user)) -> User:
    """403, not 401: the caller IS authenticated, they're just not allowed."""
    if user.role != UserRole.OPS.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ops privileges required",
        )
    return user


# Old name kept so existing routers keep working.
require_admin = require_ops


def assert_may_move_rider(user: User, rider_id: int) -> None:
    """The PERMITTED-ACTOR guard for location writes (G01).

    Location is not a harmless field. `update_rider_location` writes through to
    the Redis geohash index, and that index IS the matching engine — so an actor
    who can move riders can decide who gets dispatched. Left unauthenticated,
    anyone could teleport the whole fleet onto one coordinate and defeat the
    distance filter, the fairness band and the two-phase claim in a single
    request. That makes this the same class of guard as
    `assert_may_change_status`, not a CRUD detail.

        ops       — may move anyone (correcting a bad GPS fix is an ops action)
        rider     — may move ONLY themselves
        customer  — never

    Raises 403; never reveals whether the rider exists to a caller who has no
    business knowing.
    """
    if user.role == UserRole.OPS.value:
        return

    if user.role == UserRole.RIDER.value:
        if user.rider_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rider account is not linked to a rider record",
            )
        if user.rider_id != rider_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You may only update your own location",
            )
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Customers may not update rider locations",
    )


def assert_may_change_status(user: User, order, new_status: OrderStatus) -> None:
    """The PERMITTED-ACTOR guard — orthogonal to the legal-transition guard.

    `transition()` answers "is PENDING → DELIVERED a legal move?". This answers
    "may THIS caller make it?". Both must pass. A state machine alone will
    happily let a customer mark their own order delivered, because the move is
    legal — it is the actor that is wrong.

        ops       — anything, including cancelling
        rider     — may advance ONLY the order assigned to them
        customer  — may not touch status at all

    Raises 403; never reveals whether the order exists to a caller who has no
    business knowing.
    """
    if user.role == UserRole.OPS.value:
        return

    if user.role == UserRole.RIDER.value:
        if user.rider_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rider account is not linked to a rider record",
            )
        if order.rider_id != user.rider_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You may only update orders assigned to you",
            )
        if new_status == OrderStatus.CANCELLED:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Riders may not cancel orders; contact ops",
            )
        return

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Customers may not change order status",
    )
