"""
Full Cases API — all recovery case endpoints including analyze, simulate, guardian, execute, verify, escalate.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.models.cases import RecoveryCase
from app.models.recovery import Diagnosis, Strategy, RecoveryAction, GuardianDecision, Escalation
from app.models.audit import CaseAuditEvent
from app.schemas.base import CaseResponse, AuditEventResponse, BaseResponse, CaseTransitionRequest
from app.schemas.recovery import (
    DiagnosisResponse, StrategyResponse, GuardianResponse,
    ExecutionResponse, VerificationResponse, ReceiptResponse,
    ManualApprovalRequest, EscalateRequest,
)
from app.services.state_machine import transition_case
from app.services.diagnosis_service import run_diagnosis
from app.services.strategy_service import run_strategy_simulation
from app.services.guardian_service import run_guardian_check, approve_case_manually, reject_case_manually
from app.services.execution_service import execute_recovery_action, verify_recovery_result
from app.services.workflow_service import run_full_recovery
from app.domain.enums import CaseState

router = APIRouter()


# ─── LIST ──────────────────────────────────────────────────────────
@router.get("", response_model=BaseResponse[List[CaseResponse]], include_in_schema=False)
@router.get("/", response_model=BaseResponse[List[CaseResponse]])
def get_cases(
    merchant_id: Optional[str] = None,
    status: Optional[CaseState] = None,
    limit: int = Query(default=50, le=500),
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(RecoveryCase)
    if merchant_id:
        query = query.filter(RecoveryCase.merchant_id == merchant_id)
    if status:
        query = query.filter(RecoveryCase.status == status)
    cases = query.order_by(RecoveryCase.created_at.desc()).offset(offset).limit(limit).all()
    total = db.query(RecoveryCase).count()
    return BaseResponse(success=True, data=cases, meta={"total": total, "limit": limit, "offset": offset})


# ─── GET SINGLE ────────────────────────────────────────────────────
@router.get("/{case_id}", response_model=BaseResponse[CaseResponse])
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return BaseResponse(success=True, data=case)


# ─── AUDIT TRAIL ───────────────────────────────────────────────────
@router.get("/{case_id}/audit", response_model=BaseResponse[List[AuditEventResponse]])
def get_case_audit(case_id: str, db: Session = Depends(get_db)):
    events = (
        db.query(CaseAuditEvent)
        .filter(CaseAuditEvent.case_id == case_id)
        .order_by(CaseAuditEvent.created_at.asc())
        .all()
    )
    return BaseResponse(success=True, data=events)


# ─── AUDIT CHAIN VERIFICATION ──────────────────────────────────────
@router.get("/{case_id}/verify-audit")
def verify_case_audit_chain_route(case_id: str, db: Session = Depends(get_db)):
    from app.services.audit_service import verify_audit_chain
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    result = verify_audit_chain(db, case_id)
    return BaseResponse(success=True, data=result)


# ─── AI ACTION RECEIPT ────────────────────────────────────────────
@router.get("/{case_id}/receipt")
def get_case_receipt(case_id: str, db: Session = Depends(get_db)):
    from app.services.audit_service import verify_audit_chain
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    diagnosis = (
        db.query(Diagnosis).filter(Diagnosis.case_id == case_id)
        .order_by(Diagnosis.created_at.desc()).first()
    )
    strategies = (
        db.query(Strategy).filter(Strategy.case_id == case_id)
        .order_by(Strategy.rank).all()
    )
    guardian_decision = (
        db.query(GuardianDecision).filter(GuardianDecision.case_id == case_id)
        .order_by(GuardianDecision.created_at.desc()).first()
    )
    last_action = (
        db.query(RecoveryAction).filter(RecoveryAction.case_id == case_id)
        .order_by(RecoveryAction.created_at.desc()).first()
    )

    import hashlib
    raw_hash_input = f"{case.case_id}:{case.amount_at_risk}:{case.status}:{case.created_at}:{case.recommended_strategy}"
    compliance_hash = hashlib.sha256(raw_hash_input.encode()).hexdigest()

    receipt = {
        "case_id": case.case_id,
        "merchant_id": case.merchant_id,
        "customer_id": case.customer_id,
        "case_type": str(case.case_type),
        "revenue_at_risk": case.amount_at_risk,
        "currency": case.currency or "INR",
        "problem": str(case.case_type).replace("_", " ").title(),
        "root_cause": case.root_cause,
        "ai_confidence": case.confidence,
        "ai_confidence_formatted": f"{(case.confidence or 0):.0%}",
        "strategies_evaluated": len(strategies),
        "selected_strategy": case.recommended_strategy,
        "strategies_matrix": [
            {
                "name": s.strategy_name,
                "label": s.strategy_label,
                "probability": s.recovery_probability,
                "operational_cost": s.operational_cost,
                "discount": s.discount_amount,
                "expected_net_recovery": s.expected_net_recovery,
                "rank": s.rank,
                "is_selected": s.is_selected == "YES",
            }
            for s in strategies
        ],
        "guardian_decision": guardian_decision.decision if guardian_decision else "PENDING",
        "guardian_reason": guardian_decision.reason if guardian_decision else None,
        "policy_checks_passed": guardian_decision.checks_passed if guardian_decision else [],
        "policy_checks_failed": guardian_decision.checks_failed if guardian_decision else [],
        "idempotency_key": last_action.idempotency_key if last_action else f"idemp_{case.case_id}",
        "execution_status": last_action.status if last_action else "NOT_EXECUTED",
        "final_result": str(case.status),
        "money_recovered": case.recovered_amount or 0.0,
        "recovery_verified": case.recovery_verified or "UNVERIFIED",
        "compliance_hash": compliance_hash,
        "certificate_id": f"CERT-{case.case_id}-{compliance_hash[:8].upper()}",
        "issued_at": datetime.now(timezone.utc).isoformat(),
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "closed_at": case.closed_at.isoformat() if case.closed_at else None,
    }
    return BaseResponse(success=True, data=receipt)


# ─── STRATEGIES ────────────────────────────────────────────────────
@router.get("/{case_id}/strategies")
def get_case_strategies(case_id: str, db: Session = Depends(get_db)):
    strategies = (
        db.query(Strategy).filter(Strategy.case_id == case_id)
        .order_by(Strategy.rank).all()
    )
    return BaseResponse(success=True, data=[{
        "id": str(s.id), "strategy_name": s.strategy_name, "strategy_label": s.strategy_label,
        "description": s.description, "recovery_probability": s.recovery_probability,
        "operational_cost": s.operational_cost, "discount_amount": s.discount_amount,
        "expected_net_recovery": s.expected_net_recovery, "rank": s.rank,
        "is_selected": s.is_selected, "ai_explanation": s.ai_explanation,
        "risk_notes": s.risk_notes,
    } for s in strategies])


# ─── GUARDIAN DECISIONS ────────────────────────────────────────────
@router.get("/{case_id}/guardian-decisions")
def get_guardian_decisions(case_id: str, db: Session = Depends(get_db)):
    decisions = (
        db.query(GuardianDecision).filter(GuardianDecision.case_id == case_id)
        .order_by(GuardianDecision.created_at.asc()).all()
    )
    return BaseResponse(success=True, data=[{
        "id": str(d.id), "proposed_action": d.proposed_action,
        "decision": d.decision, "reason": d.reason,
        "checks_passed": d.checks_passed, "checks_failed": d.checks_failed,
        "decided_by": d.decided_by, "human_approver": d.human_approver,
        "created_at": d.created_at.isoformat() if d.created_at else None,
    } for d in decisions])


# ─── ANALYZE (DIAGNOSE) ────────────────────────────────────────────
@router.post("/{case_id}/analyze")
def analyze_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    result = run_diagnosis(db, case)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return BaseResponse(success=True, data=result)


# ─── SIMULATE STRATEGIES ───────────────────────────────────────────
@router.post("/{case_id}/simulate")
def simulate_strategies(case_id: str, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    result = run_strategy_simulation(db, case)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return BaseResponse(success=True, data=result)


# ─── GUARDIAN CHECK ────────────────────────────────────────────────
@router.post("/{case_id}/guardian-check")
def guardian_check(
    case_id: str,
    proposed_action: Optional[str] = Body(default=None, embed=True),
    db: Session = Depends(get_db),
):
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    result = run_guardian_check(db, case, proposed_action)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return BaseResponse(success=True, data=result)


# ─── EXECUTE ───────────────────────────────────────────────────────
@router.post("/{case_id}/execute")
def execute_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    result = execute_recovery_action(db, case)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return BaseResponse(success=True, data=result)


# ─── VERIFY ────────────────────────────────────────────────────────
@router.post("/{case_id}/verify")
def verify_case(case_id: str, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    result = verify_recovery_result(db, case)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return BaseResponse(success=True, data=result)


# ─── FULL WORKFLOW (single endpoint for complete loop) ─────────────
@router.post("/{case_id}/run")
def run_case_workflow(case_id: str, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    result = run_full_recovery(db, case)
    return BaseResponse(success=True, data=result)


# ─── ESCALATE ──────────────────────────────────────────────────────
@router.post("/{case_id}/escalate")
def escalate_case(
    case_id: str,
    reason: str = Body(default="Manual escalation", embed=True),
    escalated_to: str = Body(default="HUMAN_AGENT", embed=True),
    db: Session = Depends(get_db),
):
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    from app.services.audit_service import record_audit_event
    prev_state = case.status
    case.status = CaseState.ESCALATED
    escalation = Escalation(
        case_id=case.case_id,
        level=5,
        level_name="LEVEL_5_HUMAN_REVIEW",
        reason=reason,
        escalated_to=escalated_to,
        status="OPEN",
    )
    record_audit_event(
        db=db,
        case_id=case.case_id,
        event_type="ESCALATION",
        previous_state=prev_state,
        new_state=CaseState.ESCALATED,
        actor_type="HUMAN",
        actor_id=escalated_to,
        reason=reason,
    )
    db.add(escalation)
    db.add(case)
    db.commit()
    return BaseResponse(success=True, data={"case_id": case.case_id, "status": "ESCALATED", "escalated_to": escalated_to})


# ─── APPROVE / REJECT ─────────────────────────────────────────────
@router.post("/{case_id}/approve")
def approve_case(
    case_id: str,
    approver_id: str = Body(default="HUMAN_AGENT", embed=True),
    notes: str = Body(default="", embed=True),
    db: Session = Depends(get_db),
):
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    result = approve_case_manually(db, case, approver_id, notes)
    return BaseResponse(success=True, data=result)


@router.post("/{case_id}/reject")
def reject_case(
    case_id: str,
    rejector_id: str = Body(default="HUMAN_AGENT", embed=True),
    reason: str = Body(default="", embed=True),
    db: Session = Depends(get_db),
):
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    result = reject_case_manually(db, case, rejector_id, reason)
    return BaseResponse(success=True, data=result)


# ─── TRANSITION (manual state override) ───────────────────────────
@router.post("/{case_id}/transition", response_model=BaseResponse[CaseResponse])
def transition_case_route(case_id: str, payload: CaseTransitionRequest, db: Session = Depends(get_db)):
    case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    try:
        updated_case = transition_case(
            db=db, case=case, new_state=payload.new_state,
            reason=payload.reason, actor_type=payload.actor_type, actor_id=payload.actor_id,
        )
        return BaseResponse(success=True, data=updated_case)
    except HTTPException as he:
        return BaseResponse(success=False, error=he.detail)
    except Exception as e:
        return BaseResponse(success=False, error=str(e))
