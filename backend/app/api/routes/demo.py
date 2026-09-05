"""
Demo Mode API — Pre-configured scenarios for demonstrations.

Runs 6 realistic scenarios showing the full power of RecoveryPilot AI:
1. Successful payment recovery
2. Checkout abandonment recovery
3. Guardian blocks unsafe action  
4. Overdue invoice escalates to human
5. Promise-to-pay broken
6. AI provider timeout → safe fallback → escalation
"""
import uuid
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.models.cases import RecoveryCase
from app.domain.enums import CaseType, CaseState, RiskLevel, Priority
from app.services.workflow_service import run_full_recovery
from app.services.diagnosis_service import run_diagnosis
from app.services.strategy_service import run_strategy_simulation
from app.services.guardian_service import run_guardian_check
from app.services.execution_service import execute_recovery_action, verify_recovery_result
from app.providers.ai_provider import MockAIProvider
from app.providers.payment_provider import MockPaymentProvider
from app.schemas.base import BaseResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def _create_demo_case(
    db: Session,
    case_type: CaseType,
    amount: float,
    merchant_id: str = "DEMO_MERCHANT",
    customer_id: str = "DEMO_CUSTOMER",
    retry_count: int = 0,
    message_count: int = 0,
    confidence_override: float = None,
    extra: dict = None,
) -> RecoveryCase:
    case_id = f"DEMO-{str(uuid.uuid4())[:8].upper()}"
    risk_level = (
        RiskLevel.CRITICAL if amount > 100000
        else RiskLevel.HIGH if amount > 50000
        else RiskLevel.MEDIUM if amount > 10000
        else RiskLevel.LOW
    )
    case = RecoveryCase(
        id=str(uuid.uuid4()),
        case_id=case_id,
        merchant_id=merchant_id,
        customer_id=customer_id,
        case_type=case_type,
        reference_id=f"REF-{str(uuid.uuid4())[:6].upper()}",
        amount_at_risk=amount,
        currency="INR",
        status=CaseState.DETECTED,
        risk_level=risk_level,
        priority=Priority.HIGH if amount > 10000 else Priority.MEDIUM,
        retry_count=retry_count,
        message_count=message_count,
        confidence=confidence_override,
        recovered_amount=0.0,
        extra_data=extra or {},
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case


@router.post("/run")
def run_demo(scenario: int = 1, db: Session = Depends(get_db)):
    """
    Run a specific demo scenario.
    
    Scenarios:
    1 = Successful payment recovery (₹30,000)
    2 = Checkout abandonment → recovery link
    3 = Guardian blocks action (max retries exceeded)
    4 = Overdue invoice → human escalation
    5 = Promise-to-pay broken → recovery workflow
    6 = AI timeout → safe fallback → escalation
    """
    if scenario == 1:
        return _scenario_1_successful_payment(db)
    elif scenario == 2:
        return _scenario_2_checkout_recovery(db)
    elif scenario == 3:
        return _scenario_3_guardian_blocks(db)
    elif scenario == 4:
        return _scenario_4_invoice_escalation(db)
    elif scenario == 5:
        return _scenario_5_broken_promise(db)
    elif scenario == 6:
        return _scenario_6_ai_timeout_fallback(db)
    else:
        return BaseResponse(success=False, error="Invalid scenario. Choose 1-6.")


@router.post("/run-all")
def run_all_demos(db: Session = Depends(get_db)):
    """Run all 6 demo scenarios and return combined results."""
    results = []
    for i in range(1, 7):
        try:
            r = run_demo(i, db)
            results.append({"scenario": i, "result": r})
        except Exception as e:
            results.append({"scenario": i, "error": str(e)})
    return BaseResponse(success=True, data=results)


def _scenario_1_successful_payment(db: Session):
    """₹30,000 payment failure → full recovery loop → RECOVERED."""
    case = _create_demo_case(db, CaseType.PAYMENT_FAILURE, 30000.0, extra={"force_success": True})
    result = run_full_recovery(db, case)
    db.refresh(case)
    return BaseResponse(success=True, data={
        "scenario": 1,
        "title": "Successful Payment Recovery",
        "description": "₹30,000 payment failure detected, diagnosed, strategy selected, Guardian approved, payment executed and verified.",
        "case_id": case.case_id,
        "amount": 30000,
        "steps": result["steps"],
        "final_status": result["final_status"],
        "recovered_amount": result["recovered_amount"],
        "demonstration": "FAILURE → DETECT → DIAGNOSE → STRATEGY → GUARDIAN APPROVED → EXECUTE → VERIFIED → ₹30,000 RECOVERED",
    })


def _scenario_2_checkout_recovery(db: Session):
    """₹7,500 cart abandoned → recovery link sent."""
    case = _create_demo_case(db, CaseType.CHECKOUT_ABANDONMENT, 7500.0, message_count=1)
    result = run_full_recovery(db, case)
    db.refresh(case)
    return BaseResponse(success=True, data={
        "scenario": 2,
        "title": "Checkout Abandonment Recovery",
        "description": "Customer abandoned ₹7,500 cart. Recovery link sent after Guardian approval.",
        "case_id": case.case_id,
        "amount": 7500,
        "steps": result["steps"],
        "final_status": result["final_status"],
        "recovered_amount": result["recovered_amount"],
        "demonstration": "CART ABANDONED → DETECT → DIAGNOSE → STRATEGY(SEND_RECOVERY_LINK) → GUARDIAN APPROVED → SENT",
    })


def _scenario_3_guardian_blocks(db: Session):
    """Retry attempted but max retries reached → Guardian BLOCKS."""
    # Max retries already hit (retry_count = 2, which is MAX_PAYMENT_RETRIES)
    case = _create_demo_case(db, CaseType.PAYMENT_FAILURE, 15000.0, retry_count=2)
    
    # Run diagnosis and strategy manually
    if case.status == CaseState.DETECTED:
        run_diagnosis(db, case)
        db.refresh(case)
    if case.status == CaseState.DIAGNOSED:
        run_strategy_simulation(db, case)
        db.refresh(case)
    
    # Guardian should block because retry_count >= MAX_PAYMENT_RETRIES
    if case.status == CaseState.STRATEGY_SELECTED:
        guardian_result = run_guardian_check(db, case, "RETRY_PAYMENT")
        db.refresh(case)

    return BaseResponse(success=True, data={
        "scenario": 3,
        "title": "Policy Guardian Blocks Unsafe Action",
        "description": "AI proposed RETRY_PAYMENT but Guardian blocked it — max retry limit (2) already reached.",
        "case_id": case.case_id,
        "proposed_action": "RETRY_PAYMENT",
        "retry_count": 2,
        "max_retries": 2,
        "guardian_decision": case.guardian_status,
        "guardian_reason": case.guardian_reason,
        "final_status": case.status,
        "demonstration": "AI PROPOSES RETRY → GUARDIAN CHECKS → BLOCKED (max retries=2/2) → AUTOMATION STOPPED → ESCALATE",
    })


def _scenario_4_invoice_escalation(db: Session):
    """₹2,50,000 invoice overdue 25 days → escalates to human."""
    case = _create_demo_case(
        db, CaseType.OVERDUE_RECEIVABLE, 250000.0,
        message_count=2,
        extra={"days_overdue": 25, "invoice_id": "INV-2026-00421"},
    )
    
    # Run diagnosis
    if case.status == CaseState.DETECTED:
        run_diagnosis(db, case)
        db.refresh(case)
    if case.status == CaseState.DIAGNOSED:
        run_strategy_simulation(db, case)
        db.refresh(case)
    
    # Guardian should require human approval for ₹2,50,000 (above HIGH_VALUE_THRESHOLD)
    if case.status == CaseState.STRATEGY_SELECTED:
        run_guardian_check(db, case)
        db.refresh(case)

    return BaseResponse(success=True, data={
        "scenario": 4,
        "title": "Overdue Invoice → Human Escalation",
        "description": "₹2,50,000 invoice 25 days overdue. Guardian requires human approval for high-value case.",
        "case_id": case.case_id,
        "amount": 250000,
        "days_overdue": 25,
        "guardian_decision": case.guardian_status,
        "guardian_reason": case.guardian_reason,
        "final_status": case.status,
        "demonstration": "INVOICE OVERDUE → DETECT → DIAGNOSE → STRATEGY → GUARDIAN: HIGH VALUE = HUMAN APPROVAL REQUIRED → ESCALATED",
    })


def _scenario_5_broken_promise(db: Session):
    """Customer promised to pay ₹50,000 by Aug 20, didn't → recovery triggered."""
    case = _create_demo_case(db, CaseType.PAYMENT_FAILURE, 50000.0, retry_count=0, message_count=1)
    result = run_full_recovery(db, case)
    db.refresh(case)
    return BaseResponse(success=True, data={
        "scenario": 5,
        "title": "Promise-to-Pay Broken",
        "description": "Customer promised ₹50,000 payment but did not pay by the promised date. Recovery workflow triggered.",
        "case_id": case.case_id,
        "promised_amount": 50000,
        "promise_status": "BROKEN",
        "steps": result["steps"],
        "final_status": result["final_status"],
        "recovered_amount": result["recovered_amount"],
        "demonstration": "PROMISE BROKEN → RECOVERY EVENT → DETECT → DIAGNOSE → STRATEGY → GUARDIAN → EXECUTE",
    })


def _scenario_6_ai_timeout_fallback(db: Session):
    """AI provider times out → deterministic fallback → safe escalation (no unsafe action taken)."""
    case = _create_demo_case(db, CaseType.PAYMENT_FAILURE, 45000.0)
    
    # Manually inject AI timeout scenario
    from app.models.recovery import Diagnosis
    import uuid as _uuid
    
    # Simulate AI failure in diagnosis (deterministic fallback)
    if case.status == CaseState.DETECTED:
        # Set very low confidence to trigger human escalation via stopping rules
        run_diagnosis(db, case)
        db.refresh(case)
        
        # Force low confidence to simulate uncertain AI
        case.confidence = 0.35  # Below MIN_AI_CONFIDENCE_FOR_AUTO_ACTION (0.60)
        db.add(case)
        db.commit()
        db.refresh(case)
    
    if case.status == CaseState.DIAGNOSED:
        run_strategy_simulation(db, case)
        db.refresh(case)
    
    if case.status == CaseState.STRATEGY_SELECTED:
        guardian_result = run_guardian_check(db, case)
        db.refresh(case)

    return BaseResponse(success=True, data={
        "scenario": 6,
        "title": "AI Provider Timeout → Safe Fallback",
        "description": "AI provider returned low-confidence result (simulating timeout/failure). Guardian blocked autonomous action. Safe escalation triggered — NO unsafe action executed.",
        "case_id": case.case_id,
        "ai_confidence": case.confidence,
        "min_confidence_threshold": 0.60,
        "guardian_decision": case.guardian_status,
        "guardian_reason": case.guardian_reason,
        "final_status": case.status,
        "unsafe_action_executed": False,
        "demonstration": "AI TIMES OUT → DETERMINISTIC FALLBACK → LOW CONFIDENCE → GUARDIAN: HUMAN_APPROVAL_REQUIRED → SAFE ESCALATION → NO UNSAFE ACTION",
    })
