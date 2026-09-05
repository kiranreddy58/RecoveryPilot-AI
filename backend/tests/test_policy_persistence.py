"""
Test Policy Guardian Configuration Persistence in SQLite

Proves that:
1. Policies updated via the API / DB are stored in the SQLite policy_configs table.
2. Across simulated restarts (fresh DB sessions/service re-instantiations), the updated policy values remain active.
3. Policy Guardian immediately enforces the updated persistent thresholds.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.core.database import Base, get_db
from app.models.policy import PolicyConfig
from app.models.cases import RecoveryCase
from app.domain.enums import CaseType, CaseState, RiskLevel, Priority
from app.services.guardian_service import run_guardian_check
from app.api.routes.guardian import get_persisted_policies

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="module")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="module")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    fastapi_app.dependency_overrides[get_db] = override_get_db
    yield TestClient(fastapi_app)
    del fastapi_app.dependency_overrides[get_db]

def test_policy_update_and_persistence(client, db_session):
    # 1. Update policy: Change MAX_PAYMENT_RETRIES from 2 to 1 and HIGH_VALUE_THRESHOLD_INR to 50000
    res = client.post("/api/v1/guardian/policies", json={
        "MAX_PAYMENT_RETRIES": 1,
        "MAX_MESSAGES": 3,
        "MIN_HOURS_BETWEEN_CONTACTS": 24,
        "MAX_RECOVERY_DAYS": 30,
        "HIGH_VALUE_THRESHOLD_INR": 50000.0,
        "MIN_AI_CONFIDENCE_FOR_AUTO_ACTION": 0.60,
        "MAX_DISCOUNT_PERCENT": 10.0,
    })
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["active_policies"]["MAX_PAYMENT_RETRIES"] == 1
    assert data["active_policies"]["HIGH_VALUE_THRESHOLD_INR"] == 50000.0

    # 2. Simulate complete restart by opening a brand new independent DB session
    new_session = TestingSessionLocal()
    persisted = get_persisted_policies(new_session)
    assert persisted["MAX_PAYMENT_RETRIES"] == 1
    assert persisted["HIGH_VALUE_THRESHOLD_INR"] == 50000.0

    # 3. Verify Policy Guardian enforces the new threshold on a ₹60,000 case (should escalate)
    case = RecoveryCase(
        case_id="TEST-PERSIST-001",
        merchant_id="MERCH_01",
        customer_id="CUST_01",
        case_type=CaseType.PAYMENT_FAILURE,
        status=CaseState.STRATEGY_SELECTED,
        amount_at_risk=60000.0,
        currency="INR",
        retry_count=0,
        message_count=0,
        confidence=0.85,
        risk_level=RiskLevel.HIGH,
        priority=Priority.HIGH,
        recommended_strategy="RETRY_PAYMENT",
    )
    new_session.add(case)
    new_session.commit()

    decision = run_guardian_check(new_session, case, proposed_action="RETRY_PAYMENT")
    assert decision["decision"] == "HUMAN_APPROVAL_REQUIRED"
    assert "₹50,000" in decision["reason"] or "50000" in decision["reason"]

    # 4. Reset policies
    res_reset = client.post("/api/v1/guardian/policies/reset")
    assert res_reset.status_code == 200
    reset_persisted = get_persisted_policies(new_session)
    assert reset_persisted["MAX_PAYMENT_RETRIES"] == 2
    assert reset_persisted["HIGH_VALUE_THRESHOLD_INR"] == 100000.0
    new_session.close()
