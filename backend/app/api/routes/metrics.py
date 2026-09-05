"""
Metrics API — Real-time recovery metrics from the database.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.cases import RecoveryCase
from app.models.recovery import RecoveryAction, GuardianDecision, Escalation
from app.models.business import BatchRun
from app.models.audit import CaseAuditEvent
from app.domain.enums import CaseState
from app.schemas.base import BaseResponse

router = APIRouter()


@router.get("", include_in_schema=False)
@router.get("/")
def get_metrics(db: Session = Depends(get_db)):
    """Get comprehensive recovery metrics."""
    total_cases = db.query(RecoveryCase).count()
    
    # Revenue
    total_revenue_at_risk = db.query(
        func.coalesce(func.sum(RecoveryCase.amount_at_risk), 0)
    ).scalar()

    total_recovered = db.query(
        func.coalesce(func.sum(RecoveryCase.recovered_amount), 0)
    ).scalar()

    # Case status breakdown
    status_counts = {}
    for status in CaseState:
        count = db.query(RecoveryCase).filter(RecoveryCase.status == status).count()
        status_counts[status.value] = count

    # Rates
    recovery_rate_amount = (
        round(total_recovered / total_revenue_at_risk * 100, 2)
        if total_revenue_at_risk else 0
    )
    recovery_rate_cases = (
        round(status_counts.get("CLOSED", 0) / total_cases * 100, 2)
        if total_cases else 0
    )

    # Guardian decisions
    total_guardian_checks = db.query(GuardianDecision).count()
    guardian_approved = db.query(GuardianDecision).filter(GuardianDecision.decision == "APPROVED").count()
    guardian_blocked = db.query(GuardianDecision).filter(GuardianDecision.decision == "BLOCKED").count()
    guardian_human = db.query(GuardianDecision).filter(GuardianDecision.decision == "HUMAN_APPROVAL_REQUIRED").count()

    # Escalations
    total_escalations = db.query(Escalation).count()
    open_escalations = db.query(Escalation).filter(Escalation.status == "OPEN").count()

    # Actions
    total_actions = db.query(RecoveryAction).count()
    successful_actions = db.query(RecoveryAction).filter(RecoveryAction.status == "VERIFIED_SUCCESS").count()
    failed_actions = db.query(RecoveryAction).filter(RecoveryAction.status == "VERIFIED_FAILURE").count()
    unknown_actions = db.query(RecoveryAction).filter(RecoveryAction.status == "UNKNOWN").count()

    # By case type
    from app.domain.enums import CaseType
    by_type = {}
    for ct in CaseType:
        cases = db.query(RecoveryCase).filter(RecoveryCase.case_type == ct).all()
        by_type[ct.value] = {
            "count": len(cases),
            "revenue_at_risk": sum(c.amount_at_risk or 0 for c in cases),
            "recovered": sum(c.recovered_amount or 0 for c in cases),
        }

    # Recent activity (last 5 cases)
    recent_cases = (
        db.query(RecoveryCase)
        .order_by(RecoveryCase.created_at.desc())
        .limit(5)
        .all()
    )

    return BaseResponse(success=True, data={
        "total_cases": total_cases,
        "total_revenue_at_risk": round(total_revenue_at_risk, 2),
        "total_recovered": round(total_recovered, 2),
        "recovery_rate_amount": recovery_rate_amount,
        "recovery_rate_cases": recovery_rate_cases,
        "status_breakdown": status_counts,
        "guardian": {
            "total_checks": total_guardian_checks,
            "approved": guardian_approved,
            "blocked": guardian_blocked,
            "human_required": guardian_human,
        },
        "escalations": {
            "total": total_escalations,
            "open": open_escalations,
        },
        "actions": {
            "total": total_actions,
            "successful": successful_actions,
            "failed": failed_actions,
            "unknown": unknown_actions,
        },
        "by_type": by_type,
        "recent_cases": [
            {
                "case_id": c.case_id,
                "case_type": c.case_type,
                "status": c.status,
                "amount_at_risk": c.amount_at_risk,
                "recovered_amount": c.recovered_amount,
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in recent_cases
        ],
    })


@router.get("/live")
def get_live_metrics(db: Session = Depends(get_db)):
    """Quick live metrics for dashboard cards."""
    total_cases = db.query(RecoveryCase).count()
    
    active = db.query(RecoveryCase).filter(
        RecoveryCase.status.notin_([CaseState.CLOSED, CaseState.RECOVERED, CaseState.STOPPED])
    ).count()

    recovered_cases = db.query(RecoveryCase).filter(
        RecoveryCase.status.in_([CaseState.RECOVERED, CaseState.CLOSED])
    ).count()

    total_revenue = db.query(func.coalesce(func.sum(RecoveryCase.amount_at_risk), 0)).scalar()
    total_money_recovered = db.query(func.coalesce(func.sum(RecoveryCase.recovered_amount), 0)).scalar()

    blocked = db.query(RecoveryCase).filter(RecoveryCase.status == CaseState.BLOCKED).count()
    escalated = db.query(RecoveryCase).filter(RecoveryCase.status == CaseState.ESCALATED).count()

    return BaseResponse(success=True, data={
        "total_cases": total_cases,
        "active_cases": active,
        "recovered_cases": recovered_cases,
        "revenue_at_risk": round(float(total_revenue), 2),
        "money_recovered": round(float(total_money_recovered), 2),
        "recovery_rate": round(float(total_money_recovered) / float(total_revenue) * 100, 1) if total_revenue else 0,
        "blocked_actions": blocked,
        "human_escalations": escalated,
    })
