import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.cases import RecoveryCase
from app.models.audit import CaseAuditEvent
from app.domain.enums import CaseState, CaseType, RiskLevel, Priority
from app.services.audit_service import (
    record_audit_event,
    verify_audit_chain,
    calculate_event_hash,
    GENESIS_HASH,
)

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

def test_audit_chain_genesis_hash(db):
    case_id = f"REC-AUDIT-{str(uuid.uuid4())[:6]}"
    case = RecoveryCase(
        case_id=case_id,
        merchant_id="MERCHANT_01",
        customer_id="CUST_01",
        case_type=CaseType.PAYMENT_FAILURE,
        reference_id="REF_01",
        amount_at_risk=15000.0,
        currency="INR",
        status=CaseState.DETECTED,
        risk_level=RiskLevel.MEDIUM,
        priority=Priority.MEDIUM,
    )
    db.add(case)
    db.commit()

    # Step 1: Genesis event
    ev1 = record_audit_event(
        db=db,
        case_id=case_id,
        event_type="CASE_CREATED",
        previous_state=None,
        new_state=CaseState.DETECTED,
        actor_type="SYSTEM",
        actor_id="INGESTION",
        reason="Case detected from payment failure",
    )
    db.commit()

    assert ev1.previous_event_hash == GENESIS_HASH
    assert len(ev1.current_event_hash) == 64

def test_audit_chain_multi_step_continuity(db):
    case_id = f"REC-AUDIT-{str(uuid.uuid4())[:6]}"
    case = RecoveryCase(
        case_id=case_id,
        merchant_id="MERCHANT_01",
        customer_id="CUST_01",
        case_type=CaseType.PAYMENT_FAILURE,
        reference_id="REF_01",
        amount_at_risk=20000.0,
        currency="INR",
        status=CaseState.DETECTED,
    )
    db.add(case)
    db.commit()

    import time
    # Step 1: Created
    ev1 = record_audit_event(db, case_id, "CASE_CREATED", None, CaseState.DETECTED, "SYSTEM", "INGESTION")
    db.commit()
    time.sleep(0.01)

    # Step 2: Diagnosed
    ev2 = record_audit_event(db, case_id, "DIAGNOSIS", CaseState.DETECTED, CaseState.DIAGNOSED, "AI_AGENT", "DIAGNOSIS_ENGINE")
    db.commit()
    time.sleep(0.01)

    # Step 3: Guardian Approved
    ev3 = record_audit_event(db, case_id, "GUARDIAN_DECISION", CaseState.DIAGNOSED, CaseState.APPROVED, "POLICY_GUARDIAN", "GUARDIAN")
    db.commit()
    db.commit()

    # Verify chain linking
    assert ev2.previous_event_hash == ev1.current_event_hash
    assert ev3.previous_event_hash == ev2.current_event_hash

    # Verify audit chain validation
    verification = verify_audit_chain(db, case_id)
    assert verification["is_valid"] is True
    assert verification["status"] == "VERIFIED"
    assert verification["events_count"] == 3
    assert verification["tamper_detected"] is False

def test_audit_chain_tamper_detection(db):
    case_id = f"REC-AUDIT-{str(uuid.uuid4())[:6]}"
    case = RecoveryCase(
        case_id=case_id,
        merchant_id="MERCHANT_01",
        customer_id="CUST_01",
        case_type=CaseType.PAYMENT_FAILURE,
        reference_id="REF_01",
        amount_at_risk=50000.0,
        currency="INR",
        status=CaseState.DETECTED,
    )
    db.add(case)
    db.commit()

    ev1 = record_audit_event(db, case_id, "CASE_CREATED", None, CaseState.DETECTED, "SYSTEM", "INGESTION")
    db.commit()
    ev2 = record_audit_event(db, case_id, "DIAGNOSIS", CaseState.DETECTED, CaseState.DIAGNOSED, "AI_AGENT", "DIAGNOSIS_ENGINE")
    db.commit()

    # Tamper with event 1 data in database
    ev1.reason = "ALTERED_UNAUTHORIZED_DATA"
    db.add(ev1)
    db.commit()

    # Audit verification should detect tampering!
    verification = verify_audit_chain(db, case_id)
    assert verification["is_valid"] is False
    assert verification["status"] == "TAMPER_DETECTED"
    assert verification["tamper_detected"] is True
    assert verification["broken_at_step"] == 1

def test_audit_chain_broken_hash_link_detection(db):
    case_id = f"REC-AUDIT-{str(uuid.uuid4())[:6]}"
    case = RecoveryCase(
        case_id=case_id,
        merchant_id="MERCHANT_01",
        customer_id="CUST_01",
        case_type=CaseType.PAYMENT_FAILURE,
        reference_id="REF_01",
        amount_at_risk=50000.0,
        currency="INR",
        status=CaseState.DETECTED,
    )
    db.add(case)
    db.commit()

    ev1 = record_audit_event(db, case_id, "CASE_CREATED", None, CaseState.DETECTED, "SYSTEM", "INGESTION")
    db.commit()
    ev2 = record_audit_event(db, case_id, "DIAGNOSIS", CaseState.DETECTED, CaseState.DIAGNOSED, "AI_AGENT", "DIAGNOSIS_ENGINE")
    db.commit()

    # Tamper with previous_event_hash in event 2
    ev2.previous_event_hash = "FORGED_HASH_VALUE_12345678901234567890123456789012"
    db.add(ev2)
    db.commit()

    verification = verify_audit_chain(db, case_id)
    assert verification["is_valid"] is False
    assert verification["tamper_detected"] is True
