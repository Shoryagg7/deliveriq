"""Order lifecycle: creation, dispatch, state transitions, idempotency.

Every /orders call carries a token now (G02). `customer_id` is derived from the
subject rather than the body, so an anonymous order is not a thing that exists.
"""

import json

from app.core.enums import Topic


def _make_rider(client, lat=28.6139, lon=77.2090, headers=None):
    r = client.post(
        "/riders",
        json={
            "name": "Suresh",
            "current_lat": lat,
            "current_lon": lon,
        },
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


def _make_order(client, lat=28.6139, lon=77.2090, headers=None):
    r = client.post(
        "/orders",
        json={
            "restaurant_id": 1,
            "value": 500,
            "pickup_lat": lat,
            "pickup_lon": lon,
            "drop_lat": 19.0760,
            "drop_lon": 72.8777,  # Mumbai drop
        },
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()["id"]


def _order_payload(value=250):
    return {
        "restaurant_id": 1, "value": value,
        "pickup_lat": 28.6139, "pickup_lon": 77.2090,
        "drop_lat": 28.7041, "drop_lon": 77.1025,
    }


# --- creation and validation ------------------------------------------------

def test_create_order(customer_client):
    r = customer_client.post("/orders", json=_order_payload(value=500))
    assert r.status_code == 201
    body = r.json()
    assert body["value"] == 500
    assert body["status"] == "PENDING"
    assert body["id"] == 1


def test_order_is_owned_by_the_caller_not_the_body(customer_client):
    """G02: a client-supplied customer_id must not be able to reassign ownership."""
    me = customer_client.get("/auth/me").json()["id"]
    body = _order_payload() | {"customer_id": me + 999}
    created = customer_client.post("/orders", json=body).json()
    assert created["customer_id"] == me


def test_anonymous_may_not_create_an_order(client):
    assert client.post("/orders", json=_order_payload()).status_code == 401


def test_invalid_value_rejected(customer_client):
    r = customer_client.post("/orders", json=_order_payload(value=-10))
    assert r.status_code == 422


def test_boundary_coordinates_accepted(customer_client):
    # south pole (-90) and antimeridian (-180/180) are valid coordinates
    r = customer_client.post(
        "/orders",
        json={
            "restaurant_id": 1,
            "value": 100,
            "pickup_lat": -90,
            "pickup_lon": -180,
            "drop_lat": 90,
            "drop_lon": 180,
        },
    )
    assert r.status_code == 201


def test_get_missing_order_404(customer_client):
    assert customer_client.get("/orders/999").status_code == 404


def test_error_envelope(customer_client):
    r = customer_client.get("/orders/999")
    assert r.status_code == 404
    assert r.json() == {"error": "ORDER_NOT_FOUND", "message": "Order 999 not found"}


# --- dispatch ---------------------------------------------------------------

def test_dispatch_assigns_rider(ops_client):
    rider_id = _make_rider(ops_client)
    order_id = _make_order(ops_client)

    r = ops_client.post("/orders/dispatch")
    assert r.status_code == 200
    assert r.json()["dispatched"] == {"order_id": order_id, "rider_id": rider_id}

    # order is now ASSIGNED
    assert ops_client.get(f"/orders/{order_id}").json()["status"] == "ASSIGNED"


def test_dispatch_writes_an_outbox_row(ops_client, outbox_rows):
    """The event is part of the dispatch contract, so assert on it.

    It now lands in the outbox rather than going straight to Kafka — written
    inside the same transaction as the order and rider, which is what closes the
    dual-write hole.
    """
    rider_id = _make_rider(ops_client)
    order_id = _make_order(ops_client)

    assert outbox_rows() == []  # nothing written before the dispatch

    ops_client.post("/orders/dispatch")

    rows = outbox_rows()
    assert len(rows) == 1
    assert rows[0].topic == Topic.ORDER_DISPATCHED.value
    # keyed by order_id → same partition → per-order ordering downstream
    assert rows[0].key == str(order_id)
    payload = json.loads(rows[0].payload)
    assert payload["order_id"] == order_id
    assert payload["rider_id"] == rider_id
    assert rows[0].published_at is None  # the relay has not run


def test_outbox_row_commits_with_the_assignment(ops_client, outbox_rows):
    """The point of the outbox: the row and the state change share a transaction.

    If the order says ASSIGNED, the event exists. There is no window where one
    landed and the other did not.
    """
    _make_rider(ops_client)
    order_id = _make_order(ops_client)
    ops_client.post("/orders/dispatch")

    assert ops_client.get(f"/orders/{order_id}").json()["status"] == "ASSIGNED"
    assert len(outbox_rows()) == 1


def test_failed_dispatch_writes_nothing(ops_client, outbox_rows):
    """No rider → no state change → no event. Announce only durable facts."""
    _make_order(ops_client)

    assert ops_client.post("/orders/dispatch").status_code == 409
    assert outbox_rows() == []


def test_busy_rider_not_dispatched_again(ops_client):
    _make_rider(ops_client)
    _make_order(ops_client)
    _make_order(ops_client)  # two orders, one rider

    first = ops_client.post("/orders/dispatch")
    assert first.status_code == 200  # rider takes order 1, goes BUSY

    second = ops_client.post("/orders/dispatch")
    assert second.status_code == 409  # orders pending but no AVAILABLE rider


def test_delivery_frees_rider(ops_client, ops_headers):
    rider_id = _make_rider(ops_client)
    order_id = _make_order(ops_client)
    ops_client.post("/orders/dispatch")  # rider BUSY

    # advance through the legal lifecycle
    ops_client.patch(f"/orders/{order_id}/status", json={"status": "PICKED_UP"}, headers=ops_headers)
    ops_client.patch(f"/orders/{order_id}/status", json={"status": "DELIVERED"}, headers=ops_headers)

    # rider is freed → a new order near the DROP can be dispatched to them
    new_order = ops_client.post(
        "/orders",
        json={
            "restaurant_id": 1,
            "value": 300,
            "pickup_lat": 19.0760,
            "pickup_lon": 72.8777,  # at the drop
            "drop_lat": 28.6,
            "drop_lon": 77.2,
        },
    ).json()["id"]

    r = ops_client.post("/orders/dispatch")
    assert r.status_code == 200
    assert r.json()["dispatched"] == {"order_id": new_order, "rider_id": rider_id}


def test_illegal_transition_rejected(ops_client, ops_headers):
    order_id = _make_order(ops_client)
    # PENDING → DELIVERED skips ASSIGNED/PICKED_UP → illegal
    r = ops_client.patch(f"/orders/{order_id}/status", json={"status": "DELIVERED"}, headers=ops_headers)
    assert r.status_code == 400


# --- idempotency ------------------------------------------------------------

def test_idempotent_retry_replays_first_response(customer_client):
    """A retried POST must return the FIRST response, not create a second order."""
    headers = {"Idempotency-Key": "retry-me"}
    first = customer_client.post("/orders", json=_order_payload(), headers=headers)
    second = customer_client.post("/orders", json=_order_payload(), headers=headers)

    assert first.status_code == 201
    assert second.json() == first.json()          # same id, same body
    assert second.headers.get("Idempotent-Replay") == "true"
    assert len(customer_client.get("/orders").json()) == 1  # only ONE order exists


def test_different_idempotency_keys_create_separate_orders(customer_client):
    a = customer_client.post("/orders", json=_order_payload(), headers={"Idempotency-Key": "a"})
    b = customer_client.post("/orders", json=_order_payload(), headers={"Idempotency-Key": "b"})
    assert a.json()["id"] != b.json()["id"]


def test_no_key_means_no_deduplication(customer_client):
    """Opt-in contract: without the header, behaviour is unchanged."""
    a = customer_client.post("/orders", json=_order_payload())
    b = customer_client.post("/orders", json=_order_payload())
    assert a.json()["id"] != b.json()["id"]


# --- priority ordering, now computed in SQL ---------------------------------

def _backdate(order_id, minutes):
    """Age an order by rewriting created_at — the aging term reads this."""
    from datetime import UTC, datetime, timedelta

    from app.models.order import Order as OrderModel
    from tests.conftest import TestingSessionLocal

    db = TestingSessionLocal()
    try:
        when = datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=minutes)
        db.query(OrderModel).filter(OrderModel.id == order_id).update(
            {"created_at": when}
        )
        db.commit()
    finally:
        db.close()


def test_higher_value_wins_when_ages_are_equal(ops_client):
    _make_rider(ops_client)
    cheap = ops_client.post("/orders", json=_order_payload(value=100)).json()["id"]
    rich = ops_client.post("/orders", json=_order_payload(value=900)).json()["id"]

    dispatched = ops_client.post("/orders/dispatch").json()["dispatched"]
    assert dispatched["order_id"] == rich, f"expected {rich} to outrank {cheap}"


def test_aging_lets_a_cheap_old_order_overtake_a_fresh_expensive_one(ops_client):
    """The anti-starvation property, and the one the SQL rewrite had to keep.

    priority = value + minutes_waited * 10. A 100-rupee order that has waited
    two hours scores 100 + 1200 = 1300, beating a brand-new 900-rupee order.
    Without aging the cheap one would sit behind every richer arrival forever.
    """
    _make_rider(ops_client)
    old_cheap = ops_client.post("/orders", json=_order_payload(value=100)).json()["id"]
    _backdate(old_cheap, minutes=120)
    ops_client.post("/orders", json=_order_payload(value=900))

    dispatched = ops_client.post("/orders/dispatch").json()["dispatched"]
    assert dispatched["order_id"] == old_cheap


def test_ordering_survives_an_unclaimable_order(ops_client):
    """If the best order has no rider, dispatch moves on instead of giving up.

    The rewrite tracks tried orders in an exclude set, because we still hold
    their row locks — re-selecting one would spin forever.
    """
    # rider is far away, reachable only from the second order's pickup
    _make_rider(ops_client, lat=19.0760, lon=72.8777)
    unreachable = ops_client.post("/orders", json=_order_payload(value=900)).json()["id"]
    reachable = _make_order(ops_client, lat=19.0760, lon=72.8777)

    dispatched = ops_client.post("/orders/dispatch").json()["dispatched"]
    assert dispatched["order_id"] == reachable, "should skip the unclaimable top order"
    assert unreachable != reachable
