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

def test_razorpay_webhook_simulator_payment_failed(client):
    payload = {
        "event_type": "payment.failed",
        "amount": 25000.0,
        "currency": "INR",
        "merchant_id": "MERCHANT_RAZORPAY_TEST",
        "customer_id": "CUST_TEST_01",
    }
    res = client.post("/api/v1/razorpay/simulate-webhook", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["webhook_event"] == "payment.failed"
    assert data["case_id"] is not None
    assert data["workflow_result"] is not None

def test_razorpay_webhook_simulator_invoice_expired(client):
    payload = {
        "event_type": "invoice.expired",
        "amount": 150000.0,  # High value -> triggers escalation
        "currency": "INR",
        "merchant_id": "MERCHANT_B2B_CORP",
        "customer_id": "CUST_B2B_02",
    }
    res = client.post("/api/v1/razorpay/simulate-webhook", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["case_id"] is not None
    assert data["workflow_result"]["final_status"] == "ESCALATED"

def test_guardian_policies_get_and_update(client):
    # Get current policies
    res = client.get("/api/v1/guardian/policies")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "active_policies" in data
    assert data["active_policies"]["MAX_PAYMENT_RETRIES"] == 2

    # Update policies
    update_payload = {
        "MAX_PAYMENT_RETRIES": 3,
        "MAX_MESSAGES": 4,
        "MIN_HOURS_BETWEEN_CONTACTS": 12,
        "MAX_RECOVERY_DAYS": 45,
        "HIGH_VALUE_THRESHOLD_INR": 75000.0,
        "MIN_AI_CONFIDENCE_FOR_AUTO_ACTION": 0.65,
        "MAX_DISCOUNT_PERCENT": 15.0,
    }
    res2 = client.post("/api/v1/guardian/policies", json=update_payload)
    assert res2.status_code == 200
    assert res2.json()["data"]["active_policies"]["HIGH_VALUE_THRESHOLD_INR"] == 75000.0

    # Reset
    res3 = client.post("/api/v1/guardian/policies/reset")
    assert res3.status_code == 200
    assert res3.json()["data"]["active_policies"]["MAX_PAYMENT_RETRIES"] == 2
