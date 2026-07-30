from app.core.enums import Topic


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


def test_boundary_coordinates_accepted(client):
    # south pole (-90) and antimeridian (-180/180) are valid coordinates
    r = client.post(
        "/orders",
        json={
            "customer_id": 1,
            "restaurant_id": 1,
            "value": 100,
            "pickup_lat": -90,
            "pickup_lon": -180,
            "drop_lat": 90,
            "drop_lon": 180,
        },
    )
    assert r.status_code == 201


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


def test_dispatch_publishes_event(client, published_events):
    """The publish is part of the dispatch contract, so assert on it.

    Without this, the autouse mock would only be silencing the producer — the
    same green-for-the-wrong-reason shape as a patch that never applied.
    """
    rider_id = _make_rider(client)
    order_id = _make_order(client)

    assert published_events == []  # nothing published before the dispatch

    client.post("/orders/dispatch")

    assert len(published_events) == 1
    event = published_events[0]
    assert event["topic"] == Topic.ORDER_DISPATCHED.value
    # keyed by order_id → same partition → per-order ordering downstream
    assert event["key"] == str(order_id)
    assert event["payload"]["order_id"] == order_id
    assert event["payload"]["rider_id"] == rider_id


def test_failed_dispatch_publishes_nothing(client, published_events):
    """No rider → no state change → no event. Announce only durable facts."""
    _make_order(client)

    assert client.post("/orders/dispatch").status_code == 409
    assert published_events == []


def test_busy_rider_not_dispatched_again(client):
    _make_rider(client)
    _make_order(client)
    _make_order(client)  # two orders, one rider

    first = client.post("/orders/dispatch")
    assert first.status_code == 200  # rider takes order 1, goes BUSY

    second = client.post("/orders/dispatch")
    assert second.status_code == 409  # orders pending but no AVAILABLE rider


def test_delivery_frees_rider(client, ops_headers):
    rider_id = _make_rider(client)
    order_id = _make_order(client)
    client.post("/orders/dispatch")  # rider BUSY

    # advance through the legal lifecycle
    client.patch(f"/orders/{order_id}/status", json={"status": "PICKED_UP"}, headers=ops_headers)
    client.patch(f"/orders/{order_id}/status", json={"status": "DELIVERED"}, headers=ops_headers)

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


def test_illegal_transition_rejected(client, ops_headers):
    order_id = _make_order(client)
    # PENDING → DELIVERED skips ASSIGNED/PICKED_UP → illegal
    r = client.patch(f"/orders/{order_id}/status", json={"status": "DELIVERED"}, headers=ops_headers)
    assert r.status_code == 400

def test_error_envelope(client):
    r = client.get("/orders/999")
    assert r.status_code == 404
    assert r.json() == {"error": "ORDER_NOT_FOUND", "message": "Order 999 not found"}


def _order_payload(value=250):
    return {
        "customer_id": 1, "restaurant_id": 1, "value": value,
        "pickup_lat": 28.6139, "pickup_lon": 77.2090,
        "drop_lat": 28.7041, "drop_lon": 77.1025,
    }


def test_idempotent_retry_replays_first_response(client):
    """A retried POST must return the FIRST response, not create a second order."""
    headers = {"Idempotency-Key": "retry-me"}
    first = client.post("/orders", json=_order_payload(), headers=headers)
    second = client.post("/orders", json=_order_payload(), headers=headers)

    assert first.status_code == 201
    assert second.json() == first.json()          # same id, same body
    assert second.headers.get("Idempotent-Replay") == "true"
    assert len(client.get("/orders").json()) == 1  # only ONE order exists


def test_different_idempotency_keys_create_separate_orders(client):
    a = client.post("/orders", json=_order_payload(), headers={"Idempotency-Key": "a"})
    b = client.post("/orders", json=_order_payload(), headers={"Idempotency-Key": "b"})
    assert a.json()["id"] != b.json()["id"]


def test_no_key_means_no_deduplication(client):
    """Opt-in contract: without the header, behaviour is unchanged."""
    a = client.post("/orders", json=_order_payload())
    b = client.post("/orders", json=_order_payload())
    assert a.json()["id"] != b.json()["id"]
