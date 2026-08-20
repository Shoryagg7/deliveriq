"""Tier 2 behaviours: read scoping (G03) and idempotency namespacing (G05).

These cover the defects that were cross-tenant leaks rather than crashes — the
kind that pass every functional test while quietly serving one user another
user's data.
"""

from app.core.enums import UserRole
from app.models.user import User
from tests.conftest import TestingSessionLocal
from tests.test_orders import _make_order, _make_rider, _order_payload


def _login(client, email, role=UserRole.CUSTOMER.value, rider_id=None):
    client.post("/auth/register", json={"email": email, "password": "somepassword123"})
    if role != UserRole.CUSTOMER.value or rider_id is not None:
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


# --- G03: order read scoping ------------------------------------------------

def test_customer_lists_only_their_own_orders(client):
    alice = _login(client, "alice@x.io")
    bob = _login(client, "bob@x.io")
    _make_order(client, headers=alice)
    _make_order(client, headers=alice)
    bob_order = _make_order(client, headers=bob)

    assert len(client.get("/orders", headers=alice).json()) == 2
    bobs = client.get("/orders", headers=bob).json()
    assert [o["id"] for o in bobs] == [bob_order]


def test_customer_cannot_read_another_customers_order_by_id(client):
    alice = _login(client, "alice2@x.io")
    bob = _login(client, "bob2@x.io")
    alice_order = _make_order(client, headers=alice)

    r = client.get(f"/orders/{alice_order}", headers=bob)
    # 404 not 403: a 403 would confirm the id exists and allow enumeration.
    assert r.status_code == 404


def test_ops_sees_every_order(client):
    ops = _login(client, "ops-scope@x.io", UserRole.OPS.value)
    alice = _login(client, "alice3@x.io")
    _make_order(client, headers=alice)
    _make_order(client, headers=ops)
    assert len(client.get("/orders", headers=ops).json()) == 2


def test_rider_sees_only_orders_assigned_to_them(client):
    ops = _login(client, "ops-rider@x.io", UserRole.OPS.value)
    rider_id = _make_rider(client, headers=ops)
    customer = _login(client, "cust-rider@x.io")
    assigned = _make_order(client, headers=customer)
    client.post("/orders/dispatch", headers=ops)
    _make_order(client, lat=1.0, lon=1.0, headers=customer)  # far away, unassigned

    rider = _login(client, "therider@x.io", UserRole.RIDER.value, rider_id=rider_id)
    visible = client.get("/orders", headers=rider).json()
    assert [o["id"] for o in visible] == [assigned]


def test_rider_without_a_linked_record_sees_nothing(client):
    """`rider_id IS NULL` must not degrade into 'match every unassigned order'."""
    ops = _login(client, "ops-orphan@x.io", UserRole.OPS.value)
    _make_order(client, headers=ops)
    orphan = _login(client, "orphan2@x.io", UserRole.RIDER.value, rider_id=None)
    assert client.get("/orders", headers=orphan).json() == []


def test_rider_roster_is_ops_only(client):
    ops = _login(client, "ops-roster@x.io", UserRole.OPS.value)
    _make_rider(client, headers=ops)
    customer = _login(client, "nosy@x.io")
    assert client.get("/riders", headers=customer).status_code == 403
    assert client.get("/riders").status_code == 401
    assert len(client.get("/riders", headers=ops).json()) == 1


# --- G05: idempotency is per-principal, and bound to the request ------------

def test_same_key_from_two_users_does_not_leak(client):
    """The cross-tenant leak: both send `Idempotency-Key: shared`."""
    alice = _login(client, "alice4@x.io")
    bob = _login(client, "bob4@x.io")
    hdr = {"Idempotency-Key": "shared"}

    a = client.post("/orders", json=_order_payload(), headers={**alice, **hdr})
    b = client.post("/orders", json=_order_payload(), headers={**bob, **hdr})

    assert a.status_code == 201 and b.status_code == 201
    assert a.json()["id"] != b.json()["id"]          # bob got his OWN order
    assert b.headers.get("Idempotent-Replay") is None
    assert b.json()["customer_id"] != a.json()["customer_id"]


def test_same_key_different_body_is_rejected_not_replayed(client):
    """A key promises 'retry of that exact call'. A different body is not one."""
    alice = _login(client, "alice5@x.io")
    hdr = {"Idempotency-Key": "reused", **alice}

    first = client.post("/orders", json=_order_payload(value=100), headers=hdr)
    assert first.status_code == 201

    second = client.post("/orders", json=_order_payload(value=999), headers=hdr)
    assert second.status_code == 422
    assert second.json()["error"] == "IDEMPOTENCY_KEY_REUSED"


def test_same_key_same_body_still_replays(client):
    """The fingerprint must not break the feature it protects."""
    alice = _login(client, "alice6@x.io")
    hdr = {"Idempotency-Key": "genuine-retry", **alice}
    first = client.post("/orders", json=_order_payload(), headers=hdr)
    second = client.post("/orders", json=_order_payload(), headers=hdr)
    assert second.json() == first.json()
    assert second.headers.get("Idempotent-Replay") == "true"


def test_request_body_survives_the_middleware(client):
    """The middleware drains the body to fingerprint it, so it must put it back.

    If the receive channel were left consumed, the route would see an empty body
    and every keyed POST would 422 on validation instead of succeeding.
    """
    alice = _login(client, "alice7@x.io")
    r = client.post(
        "/orders",
        json=_order_payload(value=777),
        headers={"Idempotency-Key": "body-intact", **alice},
    )
    assert r.status_code == 201
    assert r.json()["value"] == 777
