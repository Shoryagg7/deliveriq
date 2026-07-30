"""Auth: registration, login, and the authn-vs-authz distinction."""


def _register(client, email="u@x.io", password="supersecret123"):
    return client.post("/auth/register", json={"email": email, "password": password})


def _token(client, email="u@x.io", password="supersecret123"):
    r = client.post("/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


def test_register_then_login_returns_token(client):
    assert _register(client).status_code == 201
    token = _token(client)
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "u@x.io"
    assert me.json()["role"] == "customer"


def test_duplicate_email_rejected(client):
    _register(client)
    assert _register(client).status_code == 409


def test_wrong_password_is_generic_401(client):
    """Same message for unknown-user and wrong-password: no enumeration oracle."""
    _register(client)
    bad_pw = client.post("/auth/login", json={"email": "u@x.io", "password": "nope1234"})
    no_user = client.post("/auth/login", json={"email": "ghost@x.io", "password": "nope1234"})
    assert bad_pw.status_code == no_user.status_code == 401
    assert bad_pw.json() == no_user.json()


def test_password_is_never_stored_or_returned(client):
    body = _register(client).json()
    assert "password" not in body and "hashed_password" not in body


def test_admin_route_requires_authentication(client):
    assert client.get("/admin/stats").status_code == 401


def test_authenticated_non_admin_gets_403_not_401(client):
    """401 = who are you; 403 = I know who you are and no."""
    _register(client)
    token = _token(client)
    r = client.get("/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_tampered_token_rejected(client):
    _register(client)
    token = _token(client)
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}x"})
    assert r.status_code == 401


# --- permitted-actor guard on status transitions (the Day-19 promise) --------

def _rider_login(client, db_session_factory, email, rider_id):
    from app.core.enums import UserRole
    from app.models.user import User
    client.post("/auth/register", json={"email": email, "password": "riderpass123"})
    db = db_session_factory()
    try:
        db.query(User).filter(User.email == email).update(
            {"role": UserRole.RIDER.value, "rider_id": rider_id}
        )
        db.commit()
    finally:
        db.close()
    token = client.post(
        "/auth/login", json={"email": email, "password": "riderpass123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_status_change_requires_authentication(client):
    from tests.test_orders import _make_order
    oid = _make_order(client)
    assert client.patch(f"/orders/{oid}/status", json={"status": "ASSIGNED"}).status_code == 401


def test_customer_may_not_change_status(client):
    from tests.test_orders import _make_order
    oid = _make_order(client)
    _register(client)
    token = _token(client)
    r = client.patch(
        f"/orders/{oid}/status",
        json={"status": "ASSIGNED"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403


def test_rider_may_not_touch_someone_elses_order(client, ops_headers):
    """A legal transition by the wrong actor is still forbidden."""
    from tests.conftest import TestingSessionLocal
    from tests.test_orders import _make_order, _make_rider
    _make_rider(client)
    # a second, far-away rider so dispatch can't pick them for this order
    other_rider = _make_rider(client, lat=19.0760, lon=72.8777)
    oid = _make_order(client)
    client.post("/orders/dispatch")  # rider 1 takes it

    headers = _rider_login(client, TestingSessionLocal, "other@x.io", rider_id=other_rider)
    r = client.patch(f"/orders/{oid}/status", json={"status": "PICKED_UP"}, headers=headers)
    assert r.status_code == 403


def test_assigned_rider_may_advance_own_order_but_not_cancel(client):
    from tests.conftest import TestingSessionLocal
    from tests.test_orders import _make_order, _make_rider
    rider_id = _make_rider(client)
    oid = _make_order(client)
    client.post("/orders/dispatch")

    headers = _rider_login(client, TestingSessionLocal, "mine@x.io", rider_id=rider_id)
    ok = client.patch(f"/orders/{oid}/status", json={"status": "PICKED_UP"}, headers=headers)
    assert ok.status_code == 200

    cancel = client.patch(f"/orders/{oid}/status", json={"status": "CANCELLED"}, headers=headers)
    assert cancel.status_code == 403
