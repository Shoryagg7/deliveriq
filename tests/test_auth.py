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
    assert me.json()["is_admin"] is False


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
