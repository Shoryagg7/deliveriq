import os

os.environ["DATABASE_URL"] = (
    "postgresql://deliveriq_user:password@localhost:5433/deliveriq_test_db"
)
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
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
_PUBLISH_CALL_SITES = (
    "app.services.dispatch",
    "app.workers.runner",  # DLQ path, shared by all three worker groups
)


@pytest.fixture(autouse=True)
def reset_state():
    """Fresh tables + fresh Redis before EVERY test → full isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    redis_client.flushdb()
    yield


@pytest.fixture(autouse=True)
def recorded_events(monkeypatch):
    """Stop tests reaching a real broker, and record what they tried to publish.

    Autouse on purpose: pollution must not depend on a future test remembering
    to opt in. The test DB's id sequence starts at 1 just like the dev DB's, so
    an unmocked run writes events whose order_ids COLLIDE with real orders —
    junk that can't be filtered out by any semantic rule afterwards.

    Recording (rather than swallowing) is what makes this coverage instead of a
    muzzle: see `published_events` and test_dispatch_publishes_event.
    """
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
