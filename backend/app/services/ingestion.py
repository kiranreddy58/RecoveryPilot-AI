from sqlalchemy.orm import Session
from datetime import datetime, timezone
import uuid
from app.models.events import RecoveryEvent
from app.models.cases import RecoveryCase
from app.models.audit import CaseAuditEvent
from app.schemas.base import EventCreate
from app.services.detection import detect_risk
from app.domain.enums import CaseState, Priority

def process_event(db: Session, payload: EventCreate) -> dict:
    # Check duplicate
    existing_event = db.query(RecoveryEvent).filter(RecoveryEvent.event_id == payload.event_id).first()
    if existing_event:
        return {"status": "duplicate", "event_id": existing_event.event_id}

    if payload.idempotency_key:
        existing_idempotent = db.query(RecoveryEvent).filter(RecoveryEvent.idempotency_key == payload.idempotency_key).first()
        if existing_idempotent:
            return {"status": "duplicate", "event_id": existing_idempotent.event_id}

    # Save event
    event = RecoveryEvent(
        event_id=payload.event_id,
        event_type=payload.event_type,
        merchant_id=payload.merchant_id,
        customer_id=payload.customer_id,
        reference_id=payload.reference_id,
        amount=payload.amount,
        currency=payload.currency,
        event_timestamp=payload.event_timestamp,
        source=payload.source,
        payload=payload.payload,
        idempotency_key=payload.idempotency_key,
        processing_status="PROCESSED",
        processed_at=datetime.now(timezone.utc)
    )
    db.add(event)
    db.flush()

    # Detect
    is_risk, case_type, risk_level = detect_risk(event.event_type, event.amount)
    
    if is_risk:
        # Check active case
        active_case = db.query(RecoveryCase).filter(
            RecoveryCase.merchant_id == event.merchant_id,
            RecoveryCase.reference_id == event.reference_id,
            RecoveryCase.status.notin_([CaseState.CLOSED, CaseState.RECOVERED])
        ).first()

        if active_case:
            from app.services.audit_service import record_audit_event
            record_audit_event(
                db=db,
                case_id=active_case.case_id,
                event_type="EVENT_ATTACHED",
                previous_state=active_case.status,
                new_state=active_case.status,
                actor_type="SYSTEM",
                actor_id="INGESTION",
                reason=f"Attached event {event.event_id}",
            )
            db.commit()
            return {"status": "attached", "case_id": active_case.case_id}
        else:
            case_id = f"REC-{datetime.now().year}-{str(uuid.uuid4())[:6].upper()}"
            priority = Priority.MEDIUM # Default priority logic can be expanded
            
            new_case = RecoveryCase(
                case_id=case_id,
                merchant_id=event.merchant_id,
                customer_id=event.customer_id,
                case_type=case_type,
                reference_id=event.reference_id,
                amount_at_risk=event.amount,
                currency=event.currency,
                status=CaseState.DETECTED,
                risk_level=risk_level,
                priority=priority,
                source_event_id=event.event_id
            )
            db.add(new_case)
            db.flush()
            
            from app.services.audit_service import record_audit_event
            record_audit_event(
                db=db,
                case_id=new_case.case_id,
                event_type="CASE_CREATED",
                previous_state=None,
                new_state=CaseState.DETECTED,
                actor_type="SYSTEM",
                actor_id="INGESTION",
                reason=f"Created from event {event.event_id}",
            )
            db.commit()
            return {"status": "created", "case_id": new_case.case_id}
            
    db.commit()
    return {"status": "ignored"}
