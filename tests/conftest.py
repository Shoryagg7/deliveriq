import os

os.environ["DATABASE_URL"] = (
    "postgresql://deliveriq_user:password@localhost:5433/deliveriq_test_db"
)
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
# JWT_SECRET has no default (G04) — app.core.config refuses to import without
# one. Set here, before any app import, so the suite doesn't depend on a
# developer's .env being present. Deterministic on purpose: a random per-run
# secret would make a token captured in one test meaningless in the next.
os.environ.setdefault(
    "JWT_SECRET", "test-only-secret-not-used-outside-the-suite-0123456789"
)
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.core.kafka_producer as kafka_producer
from app.core.database import Base, get_db
from app.core.enums import UserRole
from app.core.redis_client import redis_client
from app.main import app
from app.models.order import Order  # noqa: F401 — register tables on Base
from app.models.outbox import OutboxEvent
from app.models.rider import Rider  # noqa: F401
from app.models.user import User  # noqa: F401

engine = create_engine(os.environ["DATABASE_URL"])
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Every module that did `from app.core.kafka_producer import publish_event` holds
# its OWN name binding, created at import time. Patching the definition site
# (app.core.kafka_producer.publish_event) leaves these untouched — the test goes
# green and the event still lands on the real broker. Patch where it is USED.
#
# monkeypatch.setattr raises AttributeError if the name isn't there, so this
# list cannot silently rot: move a publish call site and the suite errors
# instead of quietly publishing for real. (It already caught one — the Day 33
# refactor moved the DLQ publish out of notification_consumer into runner.)
# Dispatch no longer publishes directly — it writes an outbox row inside its
# transaction and the relay publishes later. So the call sites that must be
# patched are the relay and the DLQ path, not the service.
_PUBLISH_CALL_SITES = (
    "app.workers.runner",        # DLQ path, shared by all three worker groups
    "app.workers.outbox_relay",  # the only producer on the dispatch path now
)


@pytest.fixture(autouse=True)
def reset_state():
    """Fresh tables + fresh Redis before EVERY test → full isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    redis_client.flushdb()
    yield


@pytest.fixture(autouse=True)
def recorded_events(request, monkeypatch):
    """Stop tests reaching a real broker, and record what they tried to publish.

    Autouse on purpose: pollution must not depend on a future test remembering
    to opt in. The test DB's id sequence starts at 1 just like the dev DB's, so
    an unmocked run writes events whose order_ids COLLIDE with real orders —
    junk that can't be filtered out by any semantic rule afterwards.

    Recording (rather than swallowing) is what makes this coverage instead of a
    muzzle: see `published_events` and test_dispatch_publishes_event.
    """
    # A test marked `real_kafka` deliberately wants the real producer: it is
    # asserting that an event survives an actual broker round trip, which is the
    # one thing the mock can never prove. Opt it out of both the patch and the
    # no-real-producer assertion below.
    if "real_kafka" in request.keywords:
        yield []
        # That test legitimately built a REAL producer, and it is a module
        # global — so without this every later test trips the
        # no-real-producer control below and errors in teardown. Drain and
        # reset it, so the control keeps meaning something for the rest of
        # the run instead of being collateral damage.
        if kafka_producer._producer is not None:
            kafka_producer._producer.flush(10.0)
            kafka_producer._producer = None
        return

    recorded: list[dict] = []

    def _record(topic, payload, key=None):
        recorded.append({"topic": topic, "payload": payload, "key": key})

    for module in _PUBLISH_CALL_SITES:
        monkeypatch.setattr(f"{module}.publish_event", _record)

    yield recorded

    # Control: if any code path built a real Producer, the mock was bypassed and
    # something published for real. Fail loudly rather than pollute silently.
    assert kafka_producer._producer is None, (
        "a real Kafka producer was created during a test — a publish call site "
        "is not covered by _PUBLISH_CALL_SITES"
    )


@pytest.fixture
def published_events(recorded_events):
    """Explicit handle on what the code under test published."""
    return recorded_events


@pytest.fixture
def outbox_rows():
    """Read the outbox directly — dispatch's event now lands here, not on Kafka."""

    def _read():
        db = TestingSessionLocal()
        try:
            return db.query(OutboxEvent).order_by(OutboxEvent.id).all()
        finally:
            db.close()

    return _read


@pytest.fixture
def client():
    """TestClient whose get_db points at the test database."""

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def ops_headers(client):
    """Bearer headers for an ops user — the role allowed to drive status."""
    client.post(
        "/auth/register",
        json={"email": "ops@deliveriq.io", "password": "opspassword123"},
    )
    db = TestingSessionLocal()
    try:
        db.query(User).filter(User.email == "ops@deliveriq.io").update(
            {"role": UserRole.OPS.value}
        )
        db.commit()
    finally:
        db.close()
    token = client.post(
        "/auth/login",
        json={"email": "ops@deliveriq.io", "password": "opspassword123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def ops_client(client, ops_headers):
    """A client already carrying an ops bearer token.

    Dispatch and rider onboarding are ops-only, so most flow tests need this.
    Mutating the shared client's default headers keeps call sites clean —
    otherwise every request in a flow test grows a headers= argument.
    """
    client.headers.update(ops_headers)
    return client


@pytest.fixture
def customer_headers(client):
    """Bearer headers for a plain customer — the default actor for order flows.

    Placing an order now requires a token (G02): `customer_id` comes from the
    subject, not the body, so there is no such thing as an anonymous order.
    """
    client.post(
        "/auth/register",
        json={"email": "customer@deliveriq.io", "password": "custpassword123"},
    )
    token = client.post(
        "/auth/login",
        json={"email": "customer@deliveriq.io", "password": "custpassword123"},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def customer_client(client, customer_headers):
    """A client already carrying a customer bearer token."""
    client.headers.update(customer_headers)
    return client
