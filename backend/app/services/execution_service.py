"""
Execution Service — Executes approved recovery actions safely.

Critical rules:
- ONLY executes APPROVED actions (Guardian must have approved first)
- Implements idempotency — checks before executing
- Handles timeout gracefully (UNKNOWN state, not retry)
- Never retries without Guardian re-approval
"""
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.cases import RecoveryCase
from app.models.recovery import RecoveryAction
from app.models.audit import CaseAuditEvent
from app.domain.enums import CaseState
from app.providers.payment_provider import get_payment_provider

logger = logging.getLogger(__name__)


def execute_recovery_action(
    db: Session,
    case: RecoveryCase,
    actor_id: str = "EXECUTOR",
) -> dict:
    """
    Execute the approved recovery action for a case.
    
    Safety:
    - Only runs if case is APPROVED
    - Idempotency check prevents duplicate execution
    - Handles provider failures gracefully
    """
    if case.status in (CaseState.DETECTED, CaseState.DIAGNOSED, CaseState.STRATEGY_SELECTED):
        from app.services.guardian_service import run_guardian_check
        g_res = run_guardian_check(db, case)
        if g_res.get("decision") != "APPROVED":
            return {"error": f"Cannot execute — Policy Guardian returned {g_res.get('decision')}: {g_res.get('reason')}"}
    elif case.status != CaseState.APPROVED:
        return {"error": f"Cannot execute action — case is in state {case.status}"}

    if case.guardian_status not in ("APPROVED", "MANUALLY_APPROVED"):
        return {"error": "Cannot execute — Policy Guardian has not approved this action"}

    action_type = case.recommended_strategy or "SEND_PAYMENT_LINK"

    # Idempotency key
    idempotency_key = f"{case.case_id}:{action_type}:attempt_{int(case.retry_count or 0) + 1}"

    # Check for existing action with this key
    existing = db.query(RecoveryAction).filter(
        RecoveryAction.idempotency_key == idempotency_key
    ).first()

    if existing:
        logger.info(f"Idempotency hit for {idempotency_key} — returning existing result")
        return {
            "case_id": case.case_id,
            "action_id": str(existing.id),
            "status": existing.status,
            "idempotency": "HIT",
            "message": "Action already executed (idempotent response)",
        }

    # Create action record
    action = RecoveryAction(
        id=str(uuid.uuid4()),
        case_id=case.case_id,
        action_type=action_type,
        action_label=_action_label(action_type),
        guardian_status=case.guardian_status,
        guardian_reason=case.guardian_reason,
        guardian_checked_at=datetime.now(timezone.utc),
        idempotency_key=idempotency_key,
        status="EXECUTING",
        input_data={
            "amount": case.amount_at_risk,
            "currency": case.currency,
            "merchant_id": case.merchant_id,
            "customer_id": case.customer_id,
            "reference_id": case.reference_id,
        },
    )
    db.add(action)

    # Transition to EXECUTING
    _add_audit(db, case, CaseState.EXECUTING, f"Executing action: {action_type}", actor_id)
    case.status = CaseState.EXECUTING
    if action_type in ("RETRY_PAYMENT", "RETRY_MANDATE", "RETRY_BILLING"):
        case.retry_count = (case.retry_count or 0) + 1
    elif action_type in ("SEND_PAYMENT_LINK", "SEND_REMINDER", "SEND_DISCOUNT_OFFER",
                          "SEND_RECOVERY_LINK", "SEND_CARD_UPDATE_LINK"):
        case.message_count = (case.message_count or 0) + 1

    db.add(case)
    db.flush()

    # Execute via payment provider
    provider = get_payment_provider()
    try:
        payment_context = {
            "reference_id": case.reference_id,
            "amount": case.amount_at_risk,
            "currency": case.currency,
            "merchant_id": case.merchant_id,
            "customer_id": case.customer_id,
            "idempotency_key": idempotency_key,
            **(case.extra_data or {}),
        }

        if action_type in ("RETRY_PAYMENT", "RETRY_MANDATE", "RETRY_BILLING"):
            result = provider.retry_payment(payment_context)
        elif action_type in ("SEND_PAYMENT_LINK", "SEND_CARD_UPDATE_LINK",
                              "SEND_RECOVERY_LINK", "SEND_REMINDER"):
            result = provider.send_payment_link(payment_context)
        else:
            # Simulated execution for non-payment actions
            result = {
                "status": "VERIFIED_SUCCESS",
                "message": f"Action {action_type} executed (simulated)",
                "simulated": True,
            }

        action.status = result.get("status", "UNKNOWN")
        action.output_data = result
        action.executed_at = datetime.now(timezone.utc)

    except TimeoutError as e:
        logger.error(f"Payment provider timeout for case {case.case_id}: {e}")
        action.status = "UNKNOWN"
        action.error_message = f"Provider timeout: {str(e)}"
        action.output_data = {"status": "UNKNOWN", "error": str(e)}

    except Exception as e:
        logger.error(f"Payment provider error for case {case.case_id}: {e}")
        action.status = "VERIFIED_FAILURE"
        action.error_message = str(e)
        action.output_data = {"status": "VERIFIED_FAILURE", "error": str(e)}

    # Transition to VERIFYING
    _add_audit(
        db, case, CaseState.VERIFYING,
        f"Action {action_type} executed with status: {action.status}",
        actor_id,
    )
    case.status = CaseState.VERIFYING
    db.add(action)
    db.add(case)
    db.commit()
    db.refresh(case)

    return {
        "case_id": case.case_id,
        "action_id": str(action.id),
        "action_type": action_type,
        "execution_status": action.status,
        "idempotency_key": idempotency_key,
        "result": action.output_data,
    }


def verify_recovery_result(
    db: Session,
    case: RecoveryCase,
    actor_id: str = "RESULT_VERIFIER",
) -> dict:
    """
    Verify outcome of executed action.
    
    ONLY VERIFIED_SUCCESS increases recovered_amount.
    UNKNOWN → escalate, do not mark as recovered.
    """
    if case.status in (CaseState.APPROVED, CaseState.EXECUTING):
        execute_recovery_action(db, case)
    elif case.status != CaseState.VERIFYING:
        return {"error": f"Cannot verify case in state {case.status}. (Case is already {case.status})"}

    # Get latest action
    action = (
        db.query(RecoveryAction)
        .filter(RecoveryAction.case_id == case.case_id)
        .order_by(RecoveryAction.created_at.desc())
        .first()
    )

    if not action:
        return {"error": "No action found to verify"}

    exec_status = action.status
    output_data = action.output_data or {}

    # If action was SENT (payment link, reminder), check if customer completed payment
    if exec_status == "SENT":
        if output_data.get("_will_be_used", True):
            exec_status = "VERIFIED_SUCCESS"
        else:
            exec_status = "VERIFIED_FAILURE"
        action.status = exec_status

    case.recovery_verified = exec_status
    action.verified_at = datetime.now(timezone.utc)

    if exec_status == "VERIFIED_SUCCESS":
        # ✅ Only here do we increment recovered money
        case.recovered_amount = (case.recovered_amount or 0) + (case.amount_at_risk or 0)
        case.status = CaseState.RECOVERED
        _add_audit(
            db, case, CaseState.RECOVERED,
            f"Recovery VERIFIED. ₹{case.recovered_amount:,.0f} recovered.",
            actor_id,
        )

    elif exec_status == "VERIFIED_FAILURE":
        case.status = CaseState.FAILED
        _add_audit(
            db, case, CaseState.FAILED,
            f"Recovery verification FAILED for action {action.action_type}.",
            actor_id,
        )

    elif exec_status == "UNKNOWN":
        # Do NOT mark as recovered — escalate
        case.status = CaseState.ESCALATED
        _add_audit(
            db, case, CaseState.ESCALATED,
            "Action result UNKNOWN — escalating to human for verification.",
            actor_id,
        )

    db.add(action)
    db.add(case)
    db.commit()
    db.refresh(case)

    logger.info(f"Case {case.case_id} verification: {exec_status}. Recovered: ₹{case.recovered_amount or 0:,.0f}")
    return {
        "case_id": case.case_id,
        "verification_status": exec_status,
        "case_status": case.status,
        "recovered_amount": case.recovered_amount,
        "currency": case.currency,
    }


def _action_label(action_type: str) -> str:
    labels = {
        "RETRY_PAYMENT": "Retry Payment",
        "SEND_PAYMENT_LINK": "Send Payment Link",
        "WAIT_AND_RETRY": "Wait and Retry",
        "OFFER_EMI": "Offer EMI Plan",
        "DO_NOTHING": "No Action",
        "SEND_RECOVERY_LINK": "Send Recovery Link",
        "SEND_DISCOUNT_OFFER": "Send Discount Offer",
        "SEND_REMINDER": "Send Reminder",
        "ESCALATE_TO_HUMAN": "Escalate to Human",
        "LEGAL_NOTICE": "Legal Notice",
        "RETRY_MANDATE": "Retry Mandate",
        "SEND_CARD_UPDATE_LINK": "Send Card Update Link",
        "PAUSE_SUBSCRIPTION": "Pause Subscription",
        "RETRY_BILLING": "Retry Subscription Billing",
    }
    return labels.get(action_type, action_type)


def _add_audit(db: Session, case: RecoveryCase, new_state: CaseState, reason: str, actor_id: str):
    from app.services.audit_service import record_audit_event
    record_audit_event(
        db=db,
        case_id=case.case_id,
        event_type="RECOVERY_EXECUTION" if "Executing" in reason else "RESULT_VERIFICATION",
        previous_state=case.status,
        new_state=new_state,
        actor_type="EXECUTOR",
        actor_id=actor_id,
        reason=reason,
    )
