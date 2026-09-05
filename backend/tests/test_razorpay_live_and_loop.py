import hmac
import hashlib
import json
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import Base, engine, get_db, SessionLocal
from app.models.cases import RecoveryCase
from app.domain.enums import CaseState, EventType
from app.core.config import get_settings

client = TestClient(app)
settings = get_settings()

def test_razorpay_webhook_signature_and_loop_closure():
    """
    Test full end-to-end Razorpay loop:
    1. Send payment.failed webhook with valid HMAC signature.
    2. Verify case is created and autonomous recovery runs (link sent).
    3. Send payment_link.paid webhook with matching reference_id.
    4. Verify case is automatically reconciled as RECOVERED with recovered money.
    """
    secret = settings.RAZORPAY_WEBHOOK_SECRET
    ref_id = f"PAY_TEST_{str(uuid.uuid4())[:8]}"
    amount_paise = 2500000  # ₹25,000

    # Step 1: Ingest payment.failed webhook
    fail_payload = {
        "entity": "event",
        "account_id": "acc_merchant_india",
        "event": "payment.failed",
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": ref_id,
                    "amount": amount_paise,
                    "currency": "INR",
                    "status": "failed",
                    "method": "upi",
                    "contact": "+919876543210",
                    "email": "customer@example.com",
                    "notes": {"reference_id": ref_id},
                }
            }
        },
    }
    fail_bytes = json.dumps(fail_payload).encode("utf-8")
    sig = hmac.new(secret.encode("utf-8"), fail_bytes, hashlib.sha256).hexdigest()

    resp = client.post(
        "/api/v1/razorpay/webhook",
        content=fail_bytes,
        headers={"X-Razorpay-Signature": sig, "Content-Type": "application/json"},
    )
    assert resp.status_code == 200
    res_data = resp.json()
    case_id = res_data["result"]["case_id"]
    assert case_id is not None

    # Step 2: Check case in database
    db = SessionLocal()
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    assert case is not None
    assert case.amount_at_risk == 25000.0

    # Step 3: Send payment_link.paid webhook
    paid_payload = {
        "entity": "event",
        "account_id": "acc_merchant_india",
        "event": "payment_link.paid",
        "contains": ["payment_link"],
        "payload": {
            "payment_link": {
                "entity": {
                    "id": f"plink_{ref_id}",
                    "amount_paid": amount_paise,
                    "currency": "INR",
                    "status": "paid",
                    "notes": {"reference_id": ref_id, "case_id": case_id},
                }
            }
        },
    }
    paid_bytes = json.dumps(paid_payload).encode("utf-8")
    paid_sig = hmac.new(secret.encode("utf-8"), paid_bytes, hashlib.sha256).hexdigest()

    resp_paid = client.post(
        "/api/v1/razorpay/webhook",
        content=paid_bytes,
        headers={"X-Razorpay-Signature": paid_sig, "Content-Type": "application/json"},
    )
    assert resp_paid.status_code == 200
    paid_data = resp_paid.json()
    assert paid_data["result"]["status"] == "RECOVERED"
    assert paid_data["result"]["recovered_amount"] == 25000.0

    # Step 4: Verify case is updated to RECOVERED in DB
    db.refresh(case)
    assert case.status == CaseState.RECOVERED
    assert case.recovery_verified == "VERIFIED_SUCCESS"
    assert case.recovered_amount == 25000.0
    db.close()
