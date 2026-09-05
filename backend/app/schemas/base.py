from typing import Optional, Any, Generic, TypeVar, List
from datetime import datetime
from pydantic import BaseModel, Field

from app.domain.enums import EventType, CaseType, CaseState, RiskLevel, Priority

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    meta: Optional[dict] = None

class EventCreate(BaseModel):
    event_id: str
    event_type: EventType
    merchant_id: str
    customer_id: str
    reference_id: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    event_timestamp: datetime
    source: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    idempotency_key: Optional[str] = None

class EventResponse(BaseModel):
    id: str
    event_id: str
    processing_status: Optional[str] = None

class CaseResponse(BaseModel):
    id: str
    case_id: str
    merchant_id: str
    customer_id: str
    case_type: CaseType
    reference_id: Optional[str]
    amount_at_risk: Optional[float]
    currency: Optional[str]
    status: CaseState
    risk_level: Optional[RiskLevel]
    priority: Optional[Priority]
    root_cause: Optional[str] = None
    confidence: Optional[float] = None
    recommended_strategy: Optional[str] = None
    guardian_status: Optional[str] = None
    guardian_reason: Optional[str] = None
    recovered_amount: Optional[float] = None
    recovery_verified: Optional[str] = None
    escalation_level: Optional[str] = None
    retry_count: Optional[float] = None
    message_count: Optional[float] = None
    stop_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class AuditEventResponse(BaseModel):
    id: str
    case_id: str
    event_type: str
    previous_state: Optional[str]
    new_state: str
    actor_type: str
    actor_id: str
    reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class CaseTransitionRequest(BaseModel):
    new_state: CaseState
    reason: str
    actor_type: str = "SYSTEM"
    actor_id: str = "SYSTEM"
