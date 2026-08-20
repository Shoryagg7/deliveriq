"""Rate-limit keying (G13), request-id adoption (G17), metrics ordering (G16)."""

from types import SimpleNamespace

from app.core.security import create_access_token
from app.middleware.rate_limiter import bucket_identity
from app.middleware.request_id import _incoming_request_id


def _request(headers=None, host="10.0.0.1"):
    """Enough of a Request for the pure key-derivation helpers."""
    return SimpleNamespace(
        headers=headers or {},
        client=SimpleNamespace(host=host) if host else None,
    )


# --- G13: the bucket cannot be rotated by the caller ------------------------

def test_api_key_header_no_longer_mints_a_bucket():
    """The bypass: rotating a client-supplied header used to reset the bucket."""
    a = bucket_identity(_request({"X-API-Key": "one"}))
    b = bucket_identity(_request({"X-API-Key": "two"}))
    assert a == b == bucket_identity(_request())


def test_authenticated_callers_key_on_their_verified_subject():
    token = create_access_token("someone@x.io")
    from_ip_1 = bucket_identity(_request({"Authorization": f"Bearer {token}"}, host="1.1.1.1"))
    from_ip_2 = bucket_identity(_request({"Authorization": f"Bearer {token}"}, host="2.2.2.2"))
    # Same user across two IPs shares one bucket — the point of identity keying.
    assert from_ip_1 == from_ip_2
    assert from_ip_1.startswith("user:")


def test_two_users_get_separate_buckets():
    a = create_access_token("a@x.io")
    b = create_access_token("b@x.io")
    assert bucket_identity(_request({"Authorization": f"Bearer {a}"})) != bucket_identity(
        _request({"Authorization": f"Bearer {b}"})
    )


def test_a_forged_token_falls_back_to_the_peer_address():
    """An unverified decode would let anyone choose their own bucket."""
    forged = create_access_token("victim@x.io") + "tampered"
    assert bucket_identity(_request({"Authorization": f"Bearer {forged}"})) == "ip:10.0.0.1"


def test_bucket_key_never_contains_the_raw_subject():
    token = create_access_token("leaky@example.com")
    assert "leaky@example.com" not in bucket_identity(
        _request({"Authorization": f"Bearer {token}"})
    )


def test_forwarded_for_is_ignored_unless_proxy_headers_are_trusted():
    """Untrusted by default: otherwise the header IS the bypass."""
    spoofed = _request({"X-Forwarded-For": "9.9.9.9"})
    assert bucket_identity(spoofed) == "ip:10.0.0.1"


def test_forwarded_for_is_honoured_when_trusted(monkeypatch):
    from app.core.config import settings
    monkeypatch.setattr(settings, "trust_proxy_headers", True)
    r = _request({"X-Forwarded-For": "9.9.9.9, 10.0.0.5"})
    assert bucket_identity(r) == "ip:9.9.9.9"  # left-most is the origin client


# --- G17: adopt an upstream trace id, but only a safe one -------------------

def test_valid_inbound_request_id_is_adopted():
    assert _incoming_request_id(_request({"X-Request-ID": "trace-abc-123"})) == "trace-abc-123"


def test_absent_request_id_is_none():
    assert _incoming_request_id(_request()) is None


def test_unsafe_request_ids_are_rejected():
    """Caller-supplied text goes into every log line for this request."""
    for bad in ["short", "has space", "new\nline", "x" * 65, "semi;colon"]:
        assert _incoming_request_id(_request({"X-Request-ID": bad})) is None


def test_response_echoes_the_adopted_id(client):
    r = client.get("/health", headers={"X-Request-ID": "endtoend-trace-1"})
    assert r.headers["X-Request-ID"] == "endtoend-trace-1"


def test_response_mints_an_id_when_none_is_supplied(client):
    assert len(client.get("/health").headers["X-Request-ID"]) == 36  # uuid4


# --- G16: metrics observes replays, which used to bypass it -----------------

def test_idempotent_replay_is_counted_in_http_metrics(customer_client):
    from tests.test_orders import _order_payload

    def _replays():
        body = customer_client.get("/metrics").text
        for line in body.splitlines():
            if line.startswith('deliveriq_http_requests_total{method="POST"') and '/orders"' in line:
                return float(line.rsplit(" ", 1)[1])
        return 0.0

    before = _replays()
    hdr = {"Idempotency-Key": "metrics-replay"}
    customer_client.post("/orders", json=_order_payload(), headers=hdr)
    customer_client.post("/orders", json=_order_payload(), headers=hdr)
    # Two requests reached the service; both must appear, replay included.
    assert _replays() - before == 2
