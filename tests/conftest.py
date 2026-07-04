import os

os.environ["DATABASE_URL"] = (
    "postgresql://deliveriq_user:password@localhost:5432/deliveriq_test_db"
)
os.environ["REDIS_URL"] = "redis://localhost:6379/15"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.redis_client import redis_client
from app.main import app
from app.models.order import Order  # noqa: F401 — register tables on Base
from app.models.rider import Rider  # noqa: F401

engine = create_engine(os.environ["DATABASE_URL"])
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def reset_state():
    """Fresh tables + fresh Redis before EVERY test → full isolation."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    redis_client.flushdb()
    yield


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
