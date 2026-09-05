"""
Strategy Service + Counterfactual Simulator

Flow: DIAGNOSED → STRATEGY_SELECTED

Generates multiple strategies, simulates expected outcomes,
calculates net recovery value, and selects the best strategy.
"""
import logging
import uuid
from sqlalchemy.orm import Session

from app.models.cases import RecoveryCase
from app.models.recovery import Strategy
from app.models.audit import CaseAuditEvent
from app.domain.enums import CaseState
from app.providers.ai_provider import get_ai_provider

logger = logging.getLogger(__name__)


def run_strategy_simulation(db: Session, case: RecoveryCase, actor_id: str = "STRATEGY_ENGINE") -> dict:
    """
    Run counterfactual strategy simulation for a case.
    
    Generates multiple strategies, calculates expected net recovery for each,
    selects the best one, and stores all results.
    """
    if case.status not in (CaseState.DIAGNOSED, CaseState.STRATEGY_SELECTED, CaseState.DETECTED, CaseState.ANALYZING):
        return {"error": f"Cannot simulate strategies for case in state {case.status}. (Case is already {case.status})"}
    if case.status in (CaseState.DETECTED, CaseState.ANALYZING):
        from app.services.diagnosis_service import run_diagnosis
        run_diagnosis(db, case)

    # Build context
    context = {
        "case_id": case.case_id,
        "event_type": _case_type_to_event_type(str(case.case_type)),
        "reference_id": case.reference_id,
        "amount": case.amount_at_risk,
        "currency": case.currency,
        "root_cause": case.root_cause,
        "confidence": case.confidence,
        "retry_count": case.retry_count or 0,
        "message_count": case.message_count or 0,
    }

    # Get AI strategy proposals
    provider = get_ai_provider()
    try:
        strategies = provider.generate_strategies(context)
    except Exception as e:
        logger.warning(f"AI strategy failed for {case.case_id}: {e}. Using defaults.")
        strategies = _default_strategies(context)

    # Delete old strategies for this case
    db.query(Strategy).filter(Strategy.case_id == case.case_id).delete()

    # Store all strategies
    strategy_records = []
    for strat in strategies:
        record = Strategy(
            id=str(uuid.uuid4()),
            case_id=case.case_id,
            strategy_name=strat.get("strategy_name"),
            strategy_label=strat.get("strategy_label"),
            description=strat.get("description"),
            recovery_probability=strat.get("recovery_probability"),
            operational_cost=strat.get("operational_cost", 0),
            discount_amount=strat.get("discount_amount", 0),
            expected_net_recovery=strat.get("expected_net_recovery"),
            rank=strat.get("rank"),
            is_selected="NO",
            ai_explanation=strat.get("ai_explanation"),
            risk_notes=strat.get("risk_notes"),
        )
        db.add(record)
        strategy_records.append(record)

    # Select best strategy (rank 1)
    best = strategy_records[0] if strategy_records else None
    if best:
        best.is_selected = "YES"

    # Update case
    case.recommended_strategy = best.strategy_name if best else None
    case.strategy_data = {
        "count": len(strategies),
        "selected": best.strategy_name if best else None,
        "strategies": [
            {
                "name": s.strategy_name,
                "label": s.strategy_label,
                "probability": s.recovery_probability,
                "net_recovery": s.expected_net_recovery,
                "rank": s.rank,
            }
            for s in strategy_records
        ],
    }
    case.status = CaseState.STRATEGY_SELECTED

    from app.services.audit_service import record_audit_event
    record_audit_event(
        db=db,
        case_id=case.case_id,
        event_type="STRATEGY_SELECTION",
        previous_state=CaseState.DIAGNOSED,
        new_state=CaseState.STRATEGY_SELECTED,
        actor_type="AI_AGENT",
        actor_id=actor_id,
        reason=f"Selected strategy: {case.recommended_strategy} from {len(strategies)} options",
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    logger.info(f"Case {case.case_id}: {len(strategies)} strategies simulated. Selected: {case.recommended_strategy}")
    return {
        "case_id": case.case_id,
        "strategies_evaluated": len(strategies),
        "selected_strategy": case.recommended_strategy,
        "strategies": [
            {
                "id": str(s.id),
                "name": s.strategy_name,
                "label": s.strategy_label,
                "description": s.description,
                "recovery_probability": s.recovery_probability,
                "operational_cost": s.operational_cost,
                "discount_amount": s.discount_amount,
                "expected_net_recovery": s.expected_net_recovery,
                "rank": s.rank,
                "is_selected": s.is_selected,
                "ai_explanation": s.ai_explanation,
            }
            for s in strategy_records
        ],
    }


def _case_type_to_event_type(case_type: str) -> str:
    mapping = {
        "PAYMENT_FAILURE": "PAYMENT_FAILED",
        "CHECKOUT_ABANDONMENT": "CHECKOUT_ABANDONED",
        "OVERDUE_RECEIVABLE": "INVOICE_OVERDUE",
        "SUBSCRIPTION_FAILURE": "SUBSCRIPTION_PAYMENT_FAILED",
        "PROMISE_TO_PAY_BROKEN": "PROMISE_TO_PAY_BROKEN",
    }
    for key, val in mapping.items():
        if key in case_type:
            return val
    return "PAYMENT_FAILED"


def _default_strategies(context: dict) -> list[dict]:
    """Fallback strategies when AI is unavailable."""
    amount = context.get("amount", 0) or 0
    return [
        {
            "strategy_name": "SEND_PAYMENT_LINK",
            "strategy_label": "Payment Link (Safe Default)",
            "description": "Send secure payment link — AI unavailable, using safe default.",
            "recovery_probability": 0.60,
            "operational_cost": 50,
            "discount_amount": 0,
            "expected_net_recovery": max(0, 0.60 * amount - 50),
            "ai_explanation": "Default strategy selected due to AI provider failure.",
            "risk_notes": "AI was unavailable. Human review recommended.",
            "rank": 1,
        },
        {
            "strategy_name": "ESCALATE_TO_HUMAN",
            "strategy_label": "Human Review",
            "description": "Escalate to human agent for manual recovery.",
            "recovery_probability": 0.70,
            "operational_cost": 500,
            "discount_amount": 0,
            "expected_net_recovery": max(0, 0.70 * amount - 500),
            "ai_explanation": "Human escalation as fallback when AI is unavailable.",
            "risk_notes": "",
            "rank": 2,
        },
    ]
