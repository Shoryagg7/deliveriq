def test_create_order(client):
    r = client.post(
        "/orders",
        json={
            "customer_id": 1,
            "restaurant_id": 1,
            "value": 500,
            "pickup_lat": 28.6139,
            "pickup_lon": 77.2090,
            "drop_lat": 28.7041,
            "drop_lon": 77.1025,
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["value"] == 500
    assert body["status"] == "PENDING"
    assert body["id"] == 1


def test_invalid_value_rejected(client):
    r = client.post(
        "/orders",
        json={
            "customer_id": 1,
            "restaurant_id": 1,
            "value": -10,
            "pickup_lat": 28.6,
            "pickup_lon": 77.2,
            "drop_lat": 28.7,
            "drop_lon": 77.3,
        },
    )
    assert r.status_code == 422


def test_get_missing_order_404(client):
    r = client.get("/orders/999")
    assert r.status_code == 404
def _make_rider(client, lat=28.6139, lon=77.2090):
    r = client.post(
        "/riders",
        json={
            "name": "Suresh",
            "current_lat": lat,
            "current_lon": lon,
        },
    )
    assert r.status_code == 201
    return r.json()["id"]


def _make_order(client, lat=28.6139, lon=77.2090):
    r = client.post(
        "/orders",
        json={
            "customer_id": 1,
            "restaurant_id": 1,
            "value": 500,
            "pickup_lat": lat,
            "pickup_lon": lon,
            "drop_lat": 19.0760,
            "drop_lon": 72.8777,  # Mumbai drop
        },
    )
    assert r.status_code == 201
    return r.json()["id"]


def test_dispatch_assigns_rider(client):
    rider_id = _make_rider(client)
    order_id = _make_order(client)

    r = client.post("/orders/dispatch")
    assert r.status_code == 200
    assert r.json()["dispatched"] == {"order_id": order_id, "rider_id": rider_id}

    # order is now ASSIGNED
    assert client.get(f"/orders/{order_id}").json()["status"] == "ASSIGNED"


def test_busy_rider_not_dispatched_again(client):
    _make_rider(client)
    _make_order(client)
    _make_order(client)  # two orders, one rider

    first = client.post("/orders/dispatch")
    assert first.status_code == 200  # rider takes order 1, goes BUSY

    second = client.post("/orders/dispatch")
    assert second.status_code == 404  # no AVAILABLE rider for order 2


def test_delivery_frees_rider(client):
    rider_id = _make_rider(client)
    order_id = _make_order(client)
    client.post("/orders/dispatch")  # rider BUSY

    # advance through the legal lifecycle
    client.patch(f"/orders/{order_id}/status", json={"status": "PICKED_UP"})
    client.patch(f"/orders/{order_id}/status", json={"status": "DELIVERED"})

    # rider is freed → a new order near the DROP can be dispatched to them
    new_order = client.post(
        "/orders",
        json={
            "customer_id": 2,
            "restaurant_id": 1,
            "value": 300,
            "pickup_lat": 19.0760,
            "pickup_lon": 72.8777,  # at the drop
            "drop_lat": 28.6,
            "drop_lon": 77.2,
        },
    ).json()["id"]

    r = client.post("/orders/dispatch")
    assert r.status_code == 200
    assert r.json()["dispatched"] == {"order_id": new_order, "rider_id": rider_id}


def test_illegal_transition_rejected(client):
    order_id = _make_order(client)
    # PENDING → DELIVERED skips ASSIGNED/PICKED_UP → illegal
    r = client.patch(f"/orders/{order_id}/status", json={"status": "DELIVERED"})
    assert r.status_code == 400
