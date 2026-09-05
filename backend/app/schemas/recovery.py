"""Additional response schemas for recovery workflow."""
from typing import Optional, Any, List
from datetime import datetime
from pydantic import BaseModel


class DiagnosisResponse(BaseModel):
    case_id: str
    root_cause: Optional[str]
    root_cause_category: Optional[str]
    root_cause_detail: Optional[str]
    confidence: Optional[float]
    fallback_used: Optional[str]
    diagnosis_id: Optional[str]


class StrategyResponse(BaseModel):
    case_id: str
    strategies_evaluated: int
    selected_strategy: Optional[str]
    strategies: Optional[List[dict]]


class GuardianResponse(BaseModel):
    case_id: str
    proposed_action: str
    decision: str
    reason: str
    checks_passed: Optional[List[str]]
    checks_failed: Optional[List[str]]
    decision_id: Optional[str]
    case_status: Optional[str]


class ExecutionResponse(BaseModel):
    case_id: str
    action_id: Optional[str]
    action_type: Optional[str]
    execution_status: Optional[str]
    idempotency_key: Optional[str]
    result: Optional[dict]


class VerificationResponse(BaseModel):
    case_id: str
    verification_status: Optional[str]
    case_status: Optional[str]
    recovered_amount: Optional[float]
    currency: Optional[str]


class ReceiptResponse(BaseModel):
    case_id: str
    revenue_at_risk: Optional[float]
    root_cause: Optional[str]
    ai_confidence: Optional[str]
    strategies_evaluated: Optional[int]
    selected_strategy: Optional[str]
    guardian_decision: Optional[str]
    final_result: Optional[str]
    money_recovered: Optional[float]


class ManualApprovalRequest(BaseModel):
    approver_id: str = "HUMAN_AGENT"
    notes: str = ""


class EscalateRequest(BaseModel):
    reason: str = "Manual escalation"
    escalated_to: str = "HUMAN_AGENT"
