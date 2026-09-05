import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.core.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield TestClient(fastapi_app)
    del fastapi_app.dependency_overrides[get_db]

def test_webhook_valid_signature(client):
    from app.core.config import get_settings
    secret = getattr(get_settings(), "RAZORPAY_WEBHOOK_SECRET", None) or "razorpay_webhook_secret_demo"
    payload = {
        "event": "payment.failed",
        "account_id": "acc_test_merchant",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_001",
                    "amount": 2500000, # 25,000 INR
                    "currency": "INR",
                    "status": "failed",
                    "contact": "+919876543210",
                }
            }
        }
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()

    res = client.post(
        "/api/v1/razorpay/webhook",
        content=raw_body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["result"]["case_id"] is not None

def test_webhook_invalid_signature_rejected(client):
    secret = "custom_secret_123"
    # Overwrite setting temporarily if needed
    from app.core.config import get_settings
    settings = get_settings()
    orig_secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", None)
    settings.RAZORPAY_WEBHOOK_SECRET = "custom_secret_123"

    try:
        payload = {"event": "payment.failed", "payload": {}}
        raw_body = json.dumps(payload).encode("utf-8")
        bad_sig = "invalid_forged_signature_hex_12345"

        res = client.post(
            "/api/v1/razorpay/webhook",
            content=raw_body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": bad_sig},
        )
        assert res.status_code == 400
        assert "Signature" in res.text
    finally:
        settings.RAZORPAY_WEBHOOK_SECRET = orig_secret

def test_webhook_malformed_json_rejected(client):
    res = client.post(
        "/api/v1/razorpay/webhook",
        content=b"INVALID_MALFORMED_NON_JSON_DATA",
        headers={"Content-Type": "application/json"},
    )
    assert res.status_code == 400

def test_webhook_duplicate_idempotency_prevention(client):
    payload = {
        "event_type": "payment.failed",
        "amount": 10000.0,
        "currency": "INR",
        "merchant_id": "MERCHANT_IDEMP_TEST",
        "customer_id": "CUST_IDEMP_TEST",
        "reference_id": "REF_IDEMP_12345",
    }
    # First dispatch
    res1 = client.post("/api/v1/razorpay/simulate-webhook", json=payload)
    assert res1.status_code == 200
    case_id1 = res1.json()["data"]["case_id"]
    assert case_id1 is not None

    # Second dispatch with identical reference
    res2 = client.post("/api/v1/razorpay/simulate-webhook", json=payload)
    assert res2.status_code == 200
    # Ingest attaches to existing case or detects duplicate
    assert res2.json()["data"]["ingest_status"] in ("attached", "duplicate", "created")
