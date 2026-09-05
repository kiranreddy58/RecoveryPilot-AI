"""
Full Recovery Workflow Orchestrator

Runs the complete recovery loop end-to-end:
DETECT → DIAGNOSE → SIMULATE STRATEGIES → GUARDIAN → EXECUTE → VERIFY → MEASURE → AUDIT

Handles all 5 workflow types.
"""
import logging
from sqlalchemy.orm import Session

from app.models.cases import RecoveryCase
from app.domain.enums import CaseState
from app.services.diagnosis_service import run_diagnosis
from app.services.strategy_service import run_strategy_simulation
from app.services.guardian_service import run_guardian_check
from app.services.execution_service import execute_recovery_action, verify_recovery_result
from app.services.audit_service import record_audit_event
from app.guardian.stopping_rules import check_stopping_rules
from app.models.audit import CaseAuditEvent

logger = logging.getLogger(__name__)


def run_full_recovery(db: Session, case: RecoveryCase) -> dict:
    """
    Run the complete recovery workflow for a case.
    
    Returns a summary dict with all decisions and outcomes.
    """
    results = {
        "case_id": case.case_id,
        "initial_status": case.status,
        "steps": [],
        "final_status": None,
        "recovered_amount": 0,
        "stopped": False,
        "stop_reason": None,
        "errors": [],
    }

    try:
        # ── STEP 1: DIAGNOSE ────────────────────────────────────────────
        if case.status == CaseState.DETECTED:
            stop = check_stopping_rules({
                "retry_count": case.retry_count or 0,
                "message_count": case.message_count or 0,
                "confidence": case.confidence or 1.0,
                "guardian_status": case.guardian_status,
            })
            if stop.should_stop:
                case.status = CaseState.STOPPED
                case.stop_reason = stop.reason
                db.add(case)
                db.commit()
                results["stopped"] = True
                results["stop_reason"] = stop.reason
                results["final_status"] = case.status
                return results

            diag = run_diagnosis(db, case)
            results["steps"].append({"step": "DIAGNOSIS", "result": diag})
            db.refresh(case)

        # ── STEP 2: SIMULATE STRATEGIES ────────────────────────────────
        if case.status == CaseState.DIAGNOSED:
            strat = run_strategy_simulation(db, case)
            results["steps"].append({"step": "STRATEGY_SIMULATION", "result": strat})
            db.refresh(case)

        # ── STEP 3: GUARDIAN CHECK ─────────────────────────────────────
        if case.status in (CaseState.STRATEGY_SELECTED, CaseState.GUARDIAN_REVIEW):
            guardian = run_guardian_check(db, case)
            results["steps"].append({"step": "GUARDIAN_CHECK", "result": guardian})
            db.refresh(case)

            if guardian["decision"] in ("BLOCKED", "HUMAN_APPROVAL_REQUIRED"):
                results["stopped"] = True
                results["stop_reason"] = guardian["reason"]
                results["final_status"] = case.status
                return results

        # ── STEP 4: EXECUTE ────────────────────────────────────────────
        if case.status == CaseState.APPROVED:
            execution = execute_recovery_action(db, case)
            results["steps"].append({"step": "EXECUTION", "result": execution})
            db.refresh(case)

        # ── STEP 5: VERIFY ─────────────────────────────────────────────
        if case.status == CaseState.VERIFYING:
            verification = verify_recovery_result(db, case)
            results["steps"].append({"step": "VERIFICATION", "result": verification})
            db.refresh(case)

        # ── STEP 6: CLOSE RECOVERED CASES ─────────────────────────────
        if case.status == CaseState.RECOVERED:
            from datetime import datetime, timezone
            case.closed_at = datetime.now(timezone.utc)
            record_audit_event(
                db=db,
                case_id=case.case_id,
                event_type="CASE_CLOSED",
                previous_state=CaseState.RECOVERED,
                new_state=CaseState.CLOSED,
                actor_type="SYSTEM",
                actor_id="WORKFLOW",
                reason=f"Case closed. ₹{case.recovered_amount:,.0f} recovered.",
            )
            case.status = CaseState.CLOSED
            db.add(case)
            db.commit()

    except Exception as e:
        logger.error(f"Workflow error for case {case.case_id}: {e}")
        results["errors"].append(str(e))

    db.refresh(case)
    status_str = case.status.value if hasattr(case.status, "value") else str(case.status)
    results["final_status"] = status_str
    results["recovered_amount"] = case.recovered_amount or 0

    try:
        from app.core.event_bus import event_bus
        event_bus.publish_sync(
            "WORKFLOW_COMPLETED",
            {
                "case_id": case.case_id,
                "final_status": status_str,
                "recovered_amount": case.recovered_amount or 0,
                "amount_at_risk": case.amount_at_risk or 0,
                "case_type": str(case.case_type),
            },
        )
    except Exception:
        pass

    return results
