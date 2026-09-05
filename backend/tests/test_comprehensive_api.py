import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.core.database import Base, get_db
from app.models.cases import RecoveryCase
from app.domain.enums import CaseState, CaseType, RiskLevel, Priority

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

def test_api_case_not_found(client):
    res = client.get("/api/v1/cases/NON_EXISTENT_CASE_9999")
    assert res.status_code == 404

def test_api_case_lifecycle_run(client, db):
    case_id = f"REC-TEST-{str(uuid.uuid4())[:6]}"
    case = RecoveryCase(
        case_id=case_id,
        merchant_id="MERCHANT_API_TEST",
        customer_id="CUST_API_TEST",
        case_type=CaseType.PAYMENT_FAILURE,
        reference_id="REF_API_01",
        amount_at_risk=25000.0,
        currency="INR",
        status=CaseState.DETECTED,
        risk_level=RiskLevel.MEDIUM,
        priority=Priority.MEDIUM,
    )
    db.add(case)
    db.commit()

    # Run complete workflow loop
    res = client.post(f"/api/v1/cases/{case_id}/run")
    assert res.status_code == 200
    data = res.json()["data"]
    assert str(data["final_status"]) in ("RECOVERED", "CLOSED", "ESCALATED", "BLOCKED", "STOPPED", "FAILED", "CaseState.CLOSED", "CaseState.RECOVERED", "CaseState.FAILED")

    # Fetch case audit
    audit_res = client.get(f"/api/v1/cases/{case_id}/audit")
    assert audit_res.status_code == 200
    events = audit_res.json()["data"]
    assert len(events) >= 1

    # Fetch verify-audit
    verify_res = client.get(f"/api/v1/cases/{case_id}/verify-audit")
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["is_valid"] is True

    # Fetch receipt
    receipt_res = client.get(f"/api/v1/cases/{case_id}/receipt")
    assert receipt_res.status_code == 200
    assert receipt_res.json()["data"]["case_id"] == case_id

def test_api_human_manual_approval_and_rejection(client, db):
    case_id = f"REC-ESCALATED-{str(uuid.uuid4())[:6]}"
    case = RecoveryCase(
        case_id=case_id,
        merchant_id="MERCHANT_ESCALATED",
        customer_id="CUST_ESCALATED",
        case_type=CaseType.OVERDUE_RECEIVABLE,
        reference_id="REF_ESC_01",
        amount_at_risk=150000.0,
        currency="INR",
        status=CaseState.ESCALATED,
        recommended_strategy="SEND_REMINDER",
    )
    db.add(case)
    db.commit()

    # Approve
    res_approve = client.post(
        f"/api/v1/cases/{case_id}/approve",
        json={"approver_id": "AGENT_RAJESH", "notes": "Approved after merchant consultation"},
    )
    assert res_approve.status_code == 200
    assert res_approve.json()["data"]["decision"] == "APPROVED"

    # Reset to escalated and test rejection
    case.status = CaseState.ESCALATED
    db.add(case)
    db.commit()

    res_reject = client.post(
        f"/api/v1/cases/{case_id}/reject",
        json={"rejector_id": "AGENT_RAJESH", "reason": "Customer unreachable"},
    )
    assert res_reject.status_code == 200
    assert res_reject.json()["data"]["decision"] == "REJECTED"

def test_api_metrics_full_response(client):
    res = client.get("/api/v1/metrics/")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "total_revenue_at_risk" in data
    assert "total_recovered" in data
    assert "recovery_rate_amount" in data
    assert "guardian" in data
    assert "status_breakdown" in data
