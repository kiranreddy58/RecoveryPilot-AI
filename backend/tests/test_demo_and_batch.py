import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.core.database import Base, get_db
import app.models

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
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

def test_demo_scenario_1_payment_recovery(client):
    res = client.post("/api/v1/demo/run?scenario=1")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["scenario"] == 1
    assert data["recovered_amount"] == 30000

def test_demo_scenario_3_guardian_blocks(client):
    res = client.post("/api/v1/demo/run?scenario=3")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["guardian_decision"] == "BLOCKED"
    assert data["final_status"] == "BLOCKED"

def test_demo_scenario_4_invoice_escalation(client):
    res = client.post("/api/v1/demo/run?scenario=4")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["final_status"] == "ESCALATED"

def test_demo_scenario_6_ai_timeout_safe_fallback(client):
    res = client.post("/api/v1/demo/run?scenario=6")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["unsafe_action_executed"] is False
    assert data["final_status"] == "ESCALATED"

def test_batch_processing_small_batch(client):
    res = client.post("/api/v1/batch/run", json={"target_count": 10})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_cases"] == 10
    assert data["processed_cases"] == 10
    assert "recovery_rate" in data
