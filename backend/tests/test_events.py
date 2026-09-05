import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid
from datetime import datetime, timezone

from app.main import app as fastapi_app
from app.core.database import Base, get_db
import app.models

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield TestClient(fastapi_app)
    del fastapi_app.dependency_overrides[get_db]

def test_create_event_duplicate(client):
    event_id = str(uuid.uuid4())
    payload = {
        "event_id": event_id,
        "event_type": "PAYMENT_FAILED",
        "merchant_id": "M1",
        "customer_id": "C1",
        "reference_id": "R1",
        "amount": 500,
        "currency": "USD",
        "event_timestamp": datetime.now(timezone.utc).isoformat(),
        "idempotency_key": event_id
    }
    
    response = client.post("/api/v1/events/", json=payload)
    assert response.status_code == 200
    assert response.json()["data"]["status"] in ["created", "attached", "ignored"]
    
    # Duplicate
    response2 = client.post("/api/v1/events/", json=payload)
    assert response2.status_code == 200
    assert response2.json()["data"]["status"] == "duplicate"
