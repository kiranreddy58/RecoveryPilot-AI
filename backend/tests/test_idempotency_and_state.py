import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi import HTTPException

from app.core.database import Base
from app.models.cases import RecoveryCase
from app.models.events import RecoveryEvent
from app.domain.enums import CaseState, CaseType, EventType
from app.services.state_machine import transition_case
from app.services.ingestion import process_event
from app.schemas.base import EventCreate
from datetime import datetime, timezone

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

def test_idempotency_exact_same_event_key(db):
    event_id = str(uuid.uuid4())
    idemp_key = f"IDEMP_KEY_{event_id}"
    
    event_data = EventCreate(
        event_id=event_id,
        event_type=EventType.PAYMENT_FAILED,
        merchant_id="MERCHANT_IDEMP",
        customer_id="CUST_IDEMP",
        reference_id="TXN_IDEMP_001",
        amount=15000.0,
        currency="INR",
        event_timestamp=datetime.now(timezone.utc),
        source="TEST",
        idempotency_key=idemp_key,
    )
    
    # Ingest 1
    res1 = process_event(db, event_data)
    assert res1["status"] in ("created", "attached")
    
    # Ingest 2 with same idempotency key
    res2 = process_event(db, event_data)
    assert res2["status"] == "duplicate"

def test_state_machine_terminal_closed_state(db):
    case = RecoveryCase(
        case_id="REC-TERM-01",
        merchant_id="MERCHANT_01",
        customer_id="CUST_01",
        case_type=CaseType.PAYMENT_FAILURE,
        reference_id="REF_TERM_01",
        amount_at_risk=5000.0,
        currency="INR",
        status=CaseState.CLOSED,
    )
    db.add(case)
    db.commit()

    # Attempt transition out of terminal CLOSED state
    with pytest.raises(HTTPException) as exc:
        transition_case(db, case, CaseState.EXECUTING, "Attempted illegal transition from CLOSED")
    assert exc.value.status_code == 400

def test_state_machine_stopped_to_closed(db):
    case = RecoveryCase(
        case_id="REC-STOP-01",
        merchant_id="MERCHANT_01",
        customer_id="CUST_01",
        case_type=CaseType.PAYMENT_FAILURE,
        reference_id="REF_STOP_01",
        amount_at_risk=5000.0,
        currency="INR",
        status=CaseState.STOPPED,
    )
    db.add(case)
    db.commit()

    # STOPPED can legally transition to CLOSED
    updated = transition_case(db, case, CaseState.CLOSED, "Closing stopped case")
    assert updated.status == CaseState.CLOSED

def test_state_machine_guardian_review_to_escalated(db):
    case = RecoveryCase(
        case_id="REC-GUAR-01",
        merchant_id="MERCHANT_01",
        customer_id="CUST_01",
        case_type=CaseType.PAYMENT_FAILURE,
        reference_id="REF_GUAR_01",
        amount_at_risk=5000.0,
        currency="INR",
        status=CaseState.GUARDIAN_REVIEW,
    )
    db.add(case)
    db.commit()

    # GUARDIAN_REVIEW can transition to ESCALATED
    updated = transition_case(db, case, CaseState.ESCALATED, "Guardian required human escalation")
    assert updated.status == CaseState.ESCALATED
