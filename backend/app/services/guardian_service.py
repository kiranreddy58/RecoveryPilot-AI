"""
Guardian Service — Orchestrates Policy Guardian check and stores results.

Flow: STRATEGY_SELECTED → GUARDIAN_REVIEW → APPROVED / BLOCKED / ESCALATED
"""
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.cases import RecoveryCase
from app.models.recovery import RecoveryAction, GuardianDecision, Escalation
from app.models.audit import CaseAuditEvent
from app.domain.enums import CaseState
from app.guardian.policy_guardian import PolicyGuardian
from app.guardian.stopping_rules import check_stopping_rules

logger = logging.getLogger(__name__)


def run_guardian_check(
    db: Session,
    case: RecoveryCase,
    proposed_action: str = None,
    actor_id: str = "POLICY_GUARDIAN",
    merchant_policies: dict = None,
) -> dict:
    """
    Run Policy Guardian check on the proposed action.
    
    Stores the decision. Updates case state.
    AI cannot bypass this function.
    """
    if case.status in (CaseState.DETECTED, CaseState.ANALYZING):
        from app.services.diagnosis_service import run_diagnosis
        from app.services.strategy_service import run_strategy_simulation
        run_diagnosis(db, case)
        run_strategy_simulation(db, case)
    elif case.status == CaseState.DIAGNOSED:
        from app.services.strategy_service import run_strategy_simulation
        run_strategy_simulation(db, case)
    elif case.status not in (CaseState.STRATEGY_SELECTED, CaseState.GUARDIAN_REVIEW, CaseState.APPROVED):
        return {"error": f"Cannot run guardian check on case in state {case.status}. (Case is already {case.status})"}

    # Transition to GUARDIAN_REVIEW
    if case.status != CaseState.GUARDIAN_REVIEW:
        _add_audit(db, case, CaseState.GUARDIAN_REVIEW, "Guardian review started", actor_id)
        case.status = CaseState.GUARDIAN_REVIEW
        db.add(case)
        db.flush()

    action = proposed_action or case.recommended_strategy or "SEND_PAYMENT_LINK"

    # Build context for guardian
    case_context = {
        "amount_at_risk": case.amount_at_risk,
        "currency": case.currency or "INR",
        "retry_count": case.retry_count or 0,
        "message_count": case.message_count or 0,
        "confidence": case.confidence or 0.5,
        "customer_opted_out": False,
        "guardian_status": case.guardian_status,
        "created_at": case.created_at,
        "case_type": str(case.case_type),
        "consecutive_failures": 0,
    }

    # Run guardian with persistent policies from database
    from app.api.routes.guardian import get_persisted_policies
    persisted_policies = get_persisted_policies(db)
    guardian = PolicyGuardian(policies=persisted_policies)
    result = guardian.check(action, case_context, merchant_policies)

    # Store guardian decision
    decision_record = GuardianDecision(
        id=str(uuid.uuid4()),
        case_id=case.case_id,
        proposed_action=action,
        decision=result.decision,
        checks_passed=result.checks_passed,
        checks_failed=result.checks_failed,
        reason=result.reason,
        policy_snapshot=result.policy_snapshot,
    )
    db.add(decision_record)

    # Update case based on decision
    case.guardian_status = result.decision
    case.guardian_reason = result.reason

    if result.decision == "APPROVED":
        case.status = CaseState.APPROVED
        _add_audit(db, case, CaseState.APPROVED, f"Guardian APPROVED: {result.reason}", actor_id)

    elif result.decision == "BLOCKED":
        case.status = CaseState.BLOCKED
        case.stop_reason = result.reason
        _add_audit(db, case, CaseState.BLOCKED, f"Guardian BLOCKED: {result.reason}", actor_id)
        # Check if should escalate
        stop_decision = check_stopping_rules(case_context)
        if stop_decision.escalate_to_human:
            _create_escalation(db, case, result.reason, 3)

    elif result.decision == "HUMAN_APPROVAL_REQUIRED":
        case.status = CaseState.ESCALATED
        _add_audit(
            db, case, CaseState.ESCALATED,
            f"Guardian requires human approval: {result.reason}",
            actor_id,
        )
        _create_escalation(db, case, result.reason, 4)

    db.add(case)
    db.commit()
    db.refresh(case)

    logger.info(f"Case {case.case_id}: Guardian decision = {result.decision} for action {action}")
    return {
        "case_id": case.case_id,
        "proposed_action": action,
        "decision": result.decision,
        "reason": result.reason,
        "checks_passed": result.checks_passed,
        "checks_failed": result.checks_failed,
        "decision_id": str(decision_record.id),
        "case_status": case.status,
    }


def approve_case_manually(
    db: Session,
    case: RecoveryCase,
    approver_id: str,
    notes: str = "",
) -> dict:
    """Human manually approves an escalated case."""
    if case.status not in (CaseState.ESCALATED, CaseState.BLOCKED):
        return {"error": f"Cannot manually approve case in state {case.status}"}

    case.status = CaseState.APPROVED
    case.guardian_status = "MANUALLY_APPROVED"

    # Record human decision
    decision_record = GuardianDecision(
        id=str(uuid.uuid4()),
        case_id=case.case_id,
        proposed_action=case.recommended_strategy or "UNKNOWN",
        decision="APPROVED",
        reason=f"Manually approved by {approver_id}. Notes: {notes}",
        decided_by="HUMAN",
        human_approver=approver_id,
    )
    db.add(decision_record)

    _add_audit(
        db, case, CaseState.APPROVED,
        f"Manually approved by human agent {approver_id}",
        approver_id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    return {
        "case_id": case.case_id,
        "decision": "APPROVED",
        "approver": approver_id,
        "status": case.status,
    }


def reject_case_manually(
    db: Session,
    case: RecoveryCase,
    rejector_id: str,
    reason: str = "",
) -> dict:
    """Human manually rejects/closes an escalated case."""
    case.status = CaseState.CLOSED
    case.stop_reason = f"Manually rejected by {rejector_id}: {reason}"

    decision_record = GuardianDecision(
        id=str(uuid.uuid4()),
        case_id=case.case_id,
        proposed_action=case.recommended_strategy or "UNKNOWN",
        decision="BLOCKED",
        reason=f"Manually rejected by {rejector_id}: {reason}",
        decided_by="HUMAN",
        human_approver=rejector_id,
    )
    db.add(decision_record)

    _add_audit(
        db, case, CaseState.CLOSED,
        f"Manually rejected and closed by {rejector_id}",
        rejector_id,
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    return {
        "case_id": case.case_id,
        "decision": "REJECTED",
        "rejector": rejector_id,
        "status": case.status,
    }


def _create_escalation(db: Session, case: RecoveryCase, reason: str, level: int):
    level_names = {
        0: "LEVEL_0_DETECT",
        1: "LEVEL_1_GENTLE_REMINDER",
        2: "LEVEL_2_ALTERNATIVE_PAYMENT",
        3: "LEVEL_3_FINAL_ATTEMPT",
        4: "LEVEL_4_STOP_AUTOMATION",
        5: "LEVEL_5_HUMAN_REVIEW",
    }
    escalation = Escalation(
        id=str(uuid.uuid4()),
        case_id=case.case_id,
        level=level,
        level_name=level_names.get(level, f"LEVEL_{level}"),
        reason=reason,
        status="OPEN",
    )
    db.add(escalation)
    case.escalation_level = level_names.get(level, f"LEVEL_{level}")


def _add_audit(db: Session, case: RecoveryCase, new_state: CaseState, reason: str, actor_id: str):
    from app.services.audit_service import record_audit_event
    record_audit_event(
        db=db,
        case_id=case.case_id,
        event_type="GUARDIAN_DECISION" if "Guardian" in reason else "STATE_TRANSITION",
        previous_state=case.status,
        new_state=new_state,
        actor_type="POLICY_GUARDIAN" if actor_id == "POLICY_GUARDIAN" else "HUMAN",
        actor_id=actor_id,
        reason=reason,
    )
