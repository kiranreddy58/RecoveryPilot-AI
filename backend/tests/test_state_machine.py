import pytest
from fastapi import HTTPException
from app.services.state_machine import transition_case
from app.models.cases import RecoveryCase
from app.domain.enums import CaseState, CaseType
import uuid

def test_valid_transition():
    case = RecoveryCase(
        case_id=str(uuid.uuid4()),
        merchant_id="M1",
        customer_id="C1",
        case_type=CaseType.PAYMENT_FAILURE,
        status=CaseState.DETECTED
    )
    
    # Mocking db since we only need add/commit
    class MockDB:
        def add(self, *args): pass
        def commit(self): pass
        def refresh(self, *args): pass

    db = MockDB()
    updated_case = transition_case(db, case, CaseState.ANALYZING, "Test reason")
    assert updated_case.status == CaseState.ANALYZING

def test_invalid_transition():
    case = RecoveryCase(
        case_id=str(uuid.uuid4()),
        merchant_id="M1",
        customer_id="C1",
        case_type=CaseType.PAYMENT_FAILURE,
        status=CaseState.DETECTED
    )
    
    class MockDB:
        def add(self, *args): pass
        def commit(self): pass
        def refresh(self, *args): pass

    db = MockDB()
    with pytest.raises(HTTPException) as excinfo:
        transition_case(db, case, CaseState.RECOVERED, "Invalid transition")
    
    assert excinfo.value.status_code == 400
