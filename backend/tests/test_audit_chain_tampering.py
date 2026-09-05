"""
Test Tamper Detection on Cryptographic Audit Hash Chain

Proves mathematically that:
1. A legitimate sequence of state transition events generates a continuous SHA-256 hash chain.
2. Direct unauthorized database manipulation of any audit record (tampering) is immediately detected.
3. Attempting to alter previous event hashes is immediately detected.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.audit import CaseAuditEvent
from app.services.audit_service import record_audit_event, verify_audit_chain, GENESIS_HASH

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

def test_tamper_detection_on_record_modification(db):
    case_id = "CASE-AUDIT-TEST-001"

    # 1. Record a sequence of 3 legitimate state transitions
    ev1 = record_audit_event(db, case_id, "DETECTED", None, "ANALYZING", "SYSTEM", "DETECTOR", "Risk detected")
    db.commit()

    ev2 = record_audit_event(db, case_id, "DIAGNOSED", "ANALYZING", "STRATEGY_SELECTED", "AI", "GROQ_LLM", "Diagnosis completed")
    db.commit()

    ev3 = record_audit_event(db, case_id, "APPROVED", "STRATEGY_SELECTED", "EXECUTING", "GUARDIAN", "POLICY_GUARDIAN", "Safe action approved")
    db.commit()

    # 2. Verify legitimate chain
    res_valid = verify_audit_chain(db, case_id)
    assert res_valid["is_valid"] is True
    assert res_valid["tamper_detected"] is False
    assert res_valid["events_count"] == 3
    assert res_valid["status"] == "VERIFIED"

    # 3. Simulate unauthorized database tampering: alter the reason of node 2
    ev2.reason = "TAMPERED: Illegitimate bypass injected"
    db.add(ev2)
    db.commit()

    # 4. Verify tampering is caught
    res_tampered = verify_audit_chain(db, case_id)
    assert res_tampered["is_valid"] is False
    assert res_tampered["tamper_detected"] is True
    assert res_tampered["status"] == "TAMPER_DETECTED"
    assert "mismatch" in res_tampered["message"].lower() or "broken" in res_tampered["message"].lower()

def test_tamper_detection_on_linkage_modification(db):
    case_id = "CASE-AUDIT-TEST-002"

    ev1 = record_audit_event(db, case_id, "DETECTED", None, "ANALYZING", "SYSTEM", "DETECTOR", "Node 1")
    db.commit()

    ev2 = record_audit_event(db, case_id, "DIAGNOSED", "ANALYZING", "STRATEGY_SELECTED", "AI", "LLM", "Node 2")
    db.commit()

    # Tamper with previous_event_hash linkage
    ev2.previous_event_hash = "deadbeef" * 8
    db.add(ev2)
    db.commit()

    res = verify_audit_chain(db, case_id)
    assert res["is_valid"] is False
    assert res["tamper_detected"] is True
    assert res["status"] == "TAMPER_DETECTED"
