"""G01 — `PATCH /riders/{id}/location` is a dispatch-integrity endpoint.

It writes through to the Redis geohash index, and that index is what dispatch
matches on. Unauthenticated, it let anyone decide who gets assigned work; these
tests pin the guard that closed it.
"""

from app.core.enums import UserRole
from app.models.user import User
from tests.conftest import TestingSessionLocal
from tests.test_orders import _make_order, _make_rider

_MOVE = {"lat": 19.0760, "lon": 72.8777}


def _login_as(client, email, role, rider_id=None):
    client.post("/auth/register", json={"email": email, "password": "somepassword123"})
    db = TestingSessionLocal()
    try:
        db.query(User).filter(User.email == email).update(
            {"role": role, "rider_id": rider_id}
        )
        db.commit()
    finally:
        db.close()
    token = client.post(
        "/auth/login", json={"email": email, "password": "somepassword123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_anonymous_may_not_move_a_rider(ops_client):
    """The hole itself: no token at all used to be enough."""
    rider_id = _make_rider(ops_client)
    r = ops_client.patch(
        f"/riders/{rider_id}/location", json=_MOVE, headers={"Authorization": ""}
    )
    assert r.status_code == 401


def test_customer_may_not_move_a_rider(client):
    """403, not 401 — we know exactly who they are, and the answer is no."""
    ops = _login_as(client, "ops1@x.io", UserRole.OPS.value)
    rider_id = _make_rider(client, headers=ops)
    cust = _login_as(client, "cust@x.io", UserRole.CUSTOMER.value)
    r = client.patch(f"/riders/{rider_id}/location", json=_MOVE, headers=cust)
    assert r.status_code == 403


def test_rider_may_move_themselves(client):
    ops = _login_as(client, "ops2@x.io", UserRole.OPS.value)
    rider_id = _make_rider(client, headers=ops)
    me = _login_as(client, "me@x.io", UserRole.RIDER.value, rider_id=rider_id)
    r = client.patch(f"/riders/{rider_id}/location", json=_MOVE, headers=me)
    assert r.status_code == 200


def test_rider_may_not_move_another_rider(client):
    """The fleet-hijack move, by an authenticated insider rather than a stranger."""
    ops = _login_as(client, "ops3@x.io", UserRole.OPS.value)
    mine = _make_rider(client, headers=ops)
    theirs = _make_rider(client, lat=19.07, lon=72.87, headers=ops)
    me = _login_as(client, "me2@x.io", UserRole.RIDER.value, rider_id=mine)
    r = client.patch(f"/riders/{theirs}/location", json=_MOVE, headers=me)
    assert r.status_code == 403


def test_ops_may_move_anyone(client):
    """Correcting a bad GPS fix is a legitimate operator action."""
    ops = _login_as(client, "ops4@x.io", UserRole.OPS.value)
    rider_id = _make_rider(client, headers=ops)
    r = client.patch(f"/riders/{rider_id}/location", json=_MOVE, headers=ops)
    assert r.status_code == 200


def test_rider_account_without_a_rider_record_is_refused(client):
    """role=rider but rider_id=None: we know they're a rider, not WHICH one."""
    ops = _login_as(client, "ops5@x.io", UserRole.OPS.value)
    rider_id = _make_rider(client, headers=ops)
    orphan = _login_as(client, "orphan@x.io", UserRole.RIDER.value, rider_id=None)
    r = client.patch(f"/riders/{rider_id}/location", json=_MOVE, headers=orphan)
    assert r.status_code == 403


def test_authorisation_precedes_existence_so_404_cannot_enumerate(client):
    """A forbidden caller gets 403 for a rider that does not exist.

    If the existence check ran first, the 404-vs-403 difference would let an
    unauthorised caller map the fleet one id at a time.
    """
    cust = _login_as(client, "snoop@x.io", UserRole.CUSTOMER.value)
    assert client.patch("/riders/424242/location", json=_MOVE, headers=cust).status_code == 403


def test_the_hijack_this_guard_prevents(client):
    """End to end: an outsider cannot steer dispatch by moving the fleet.

    A far-away rider is teleported onto the order's pickup point. If the move
    were permitted, the geohash index would hand them the dispatch; refused, the
    genuinely-nearest rider still wins.
    """
    ops = _login_as(client, "ops6@x.io", UserRole.OPS.value)
    near = _make_rider(client, lat=28.6139, lon=77.2090, headers=ops)
    far = _make_rider(client, lat=19.0760, lon=72.8777, headers=ops)

    attacker = _login_as(client, "attacker@x.io", UserRole.CUSTOMER.value)
    hijack = client.patch(
        f"/riders/{far}/location",
        json={"lat": 28.6139, "lon": 77.2090},  # onto the pickup
        headers=attacker,
    )
    assert hijack.status_code == 403

    _make_order(client, lat=28.6139, lon=77.2090, headers=ops)
    dispatched = client.post("/orders/dispatch", headers=ops).json()["dispatched"]
    assert dispatched["rider_id"] == near
