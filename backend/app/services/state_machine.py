from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.cases import RecoveryCase
from app.domain.enums import CaseState
from app.services.audit_service import record_audit_event

# Define valid transitions
VALID_TRANSITIONS = {
    CaseState.DETECTED: [CaseState.ANALYZING, CaseState.ESCALATED, CaseState.STOPPED],
    CaseState.ANALYZING: [CaseState.DIAGNOSED, CaseState.FAILED, CaseState.STOPPED],
    CaseState.DIAGNOSED: [CaseState.STRATEGY_SELECTED, CaseState.ESCALATED, CaseState.STOPPED],
    CaseState.STRATEGY_SELECTED: [CaseState.GUARDIAN_REVIEW, CaseState.APPROVED, CaseState.STOPPED],
    CaseState.GUARDIAN_REVIEW: [CaseState.APPROVED, CaseState.BLOCKED, CaseState.ESCALATED, CaseState.STOPPED],
    CaseState.APPROVED: [CaseState.EXECUTING, CaseState.STOPPED],
    CaseState.EXECUTING: [CaseState.VERIFYING, CaseState.FAILED, CaseState.STOPPED],
    CaseState.VERIFYING: [CaseState.RECOVERED, CaseState.FAILED, CaseState.STOPPED],
    CaseState.RECOVERED: [CaseState.CLOSED],
    CaseState.FAILED: [CaseState.ESCALATED, CaseState.CLOSED],
    CaseState.ESCALATED: [CaseState.CLOSED, CaseState.APPROVED, CaseState.STOPPED],
    CaseState.STOPPED: [CaseState.CLOSED],
    CaseState.BLOCKED: [CaseState.CLOSED, CaseState.ESCALATED],
    CaseState.CLOSED: [],
}

def transition_case(db: Session, case: RecoveryCase, new_state: CaseState, reason: str, actor_type: str = "SYSTEM", actor_id: str = "SYSTEM"):
    if new_state not in VALID_TRANSITIONS.get(case.status, []):
        raise HTTPException(status_code=400, detail=f"Invalid transition from {case.status} to {new_state}")
    
    prev_state = case.status
    case.status = new_state
    
    record_audit_event(
        db=db,
        case_id=case.case_id,
        event_type="STATE_TRANSITION",
        previous_state=prev_state,
        new_state=new_state,
        actor_type=actor_type,
        actor_id=actor_id,
        reason=reason,
    )
    
    db.add(case)
    db.commit()
    db.refresh(case)

    # Broadcast to real-time SSE stream
    try:
        from app.core.event_bus import event_bus
        event_bus.publish_sync(
            "CASE_TRANSITION",
            {
                "case_id": case.case_id,
                "previous_state": str(prev_state),
                "new_state": str(new_state),
                "amount": case.amount_at_risk,
                "recovered_amount": case.recovered_amount or 0,
                "reason": reason,
                "actor_id": actor_id,
            },
        )
    except Exception:
        pass

    return case
