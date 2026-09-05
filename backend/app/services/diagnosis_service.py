"""
Diagnosis Service — Orchestrates AI-powered root cause analysis.

Flow: DETECTED → ANALYZING → DIAGNOSED
"""
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.cases import RecoveryCase
from app.models.recovery import Diagnosis
from app.models.audit import CaseAuditEvent
from app.domain.enums import CaseState
from app.providers.ai_provider import get_ai_provider

logger = logging.getLogger(__name__)


def run_diagnosis(db: Session, case: RecoveryCase, actor_id: str = "DIAGNOSIS_ENGINE") -> dict:
    """
    Run AI diagnosis on a recovery case.
    
    Returns dict with diagnosis result.
    Handles AI failure gracefully with deterministic fallback.
    """
    if case.status not in (CaseState.DETECTED, CaseState.ANALYZING, CaseState.DIAGNOSED, CaseState.STRATEGY_SELECTED):
        return {"error": f"Cannot diagnose case in state {case.status}. (Case is already {case.status})"}

    # Transition to ANALYZING
    _add_audit(db, case, CaseState.ANALYZING, "Diagnosis started", actor_id)
    case.status = CaseState.ANALYZING
    db.add(case)
    db.flush()

    # Build context for AI
    context = {
        "case_id": case.case_id,
        "event_type": str(case.case_type).replace("CaseType.", ""),
        "reference_id": case.reference_id,
        "amount": case.amount_at_risk,
        "currency": case.currency,
        "merchant_id": case.merchant_id,
        "customer_id": case.customer_id,
        "created_at": str(case.created_at),
    }

    # Call AI provider
    provider = get_ai_provider()
    fallback_used = None
    try:
        result = provider.analyze_root_cause(context)
    except Exception as e:
        logger.warning(f"AI provider failed for case {case.case_id}: {e}. Using deterministic fallback.")
        result = _deterministic_fallback(case)
        result["fallback_used"] = "deterministic"
        fallback_used = "deterministic"

    # Store diagnosis
    diagnosis = Diagnosis(
        id=str(uuid.uuid4()),
        case_id=case.case_id,
        root_cause=result.get("root_cause", "Unknown"),
        root_cause_category=result.get("root_cause_category", "UNKNOWN"),
        root_cause_detail=result.get("root_cause_detail", ""),
        confidence=result.get("confidence", 0.5),
        ai_provider=result.get("ai_provider", "UNKNOWN"),
        ai_model=result.get("ai_model"),
        raw_ai_response=result,
        fallback_used=fallback_used,
        input_data=context,
    )
    db.add(diagnosis)

    # Update case
    case.root_cause = result.get("root_cause", "Unknown")
    case.root_cause_detail = result.get("root_cause_detail", "")
    case.confidence = result.get("confidence", 0.5)
    case.status = CaseState.DIAGNOSED

    _add_audit(
        db, case, CaseState.DIAGNOSED,
        f"Root cause: {case.root_cause} (confidence: {case.confidence:.0%})",
        actor_id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    logger.info(f"Case {case.case_id} diagnosed: {case.root_cause} ({case.confidence:.0%})")
    return {
        "case_id": case.case_id,
        "root_cause": case.root_cause,
        "root_cause_category": result.get("root_cause_category"),
        "root_cause_detail": case.root_cause_detail,
        "confidence": case.confidence,
        "fallback_used": fallback_used,
        "diagnosis_id": str(diagnosis.id),
    }


def _deterministic_fallback(case: RecoveryCase) -> dict:
    """Deterministic diagnosis when AI is unavailable."""
    case_type = str(case.case_type)
    
    fallback_map = {
        "PAYMENT_FAILURE": {
            "root_cause": "Payment processing error (deterministic fallback)",
            "root_cause_category": "TECHNICAL",
            "root_cause_detail": "AI unavailable. Deterministic fallback: Payment failure detected. Manual review recommended.",
            "confidence": 0.50,
        },
        "CHECKOUT_ABANDONMENT": {
            "root_cause": "Checkout not completed (deterministic fallback)",
            "root_cause_category": "BEHAVIOURAL",
            "root_cause_detail": "AI unavailable. Customer did not complete checkout within timeout window.",
            "confidence": 0.50,
        },
        "OVERDUE_RECEIVABLE": {
            "root_cause": "Invoice payment delayed (deterministic fallback)",
            "root_cause_category": "FINANCIAL",
            "root_cause_detail": "AI unavailable. Invoice past due date.",
            "confidence": 0.50,
        },
    }
    
    for key, val in fallback_map.items():
        if key in case_type:
            return {**val, "ai_provider": "DETERMINISTIC", "ai_model": "fallback-v1"}
    
    return {
        "root_cause": "Unknown cause (deterministic fallback)",
        "root_cause_category": "UNKNOWN",
        "root_cause_detail": "AI unavailable. No deterministic rule matched.",
        "confidence": 0.40,
        "ai_provider": "DETERMINISTIC",
        "ai_model": "fallback-v1",
    }


def _add_audit(db: Session, case: RecoveryCase, new_state: CaseState, reason: str, actor_id: str):
    from app.services.audit_service import record_audit_event
    record_audit_event(
        db=db,
        case_id=case.case_id,
        event_type="DIAGNOSIS" if "Root cause" in reason else "STATE_TRANSITION",
        previous_state=case.status,
        new_state=new_state,
        actor_type="AI_AGENT",
        actor_id=actor_id,
        reason=reason,
    )
