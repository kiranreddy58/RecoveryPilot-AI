import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Enum as SAEnum, Text, JSON

from app.core.database import Base
from app.domain.enums import CaseType, CaseState, RiskLevel, Priority

class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, unique=True, index=True, nullable=False)
    merchant_id = Column(String, nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)
    case_type = Column(SAEnum(CaseType), nullable=False)
    reference_id = Column(String, nullable=True)
    amount_at_risk = Column(Float, nullable=True)
    currency = Column(String, nullable=True, default="INR")
    status = Column(SAEnum(CaseState), nullable=False, default=CaseState.DETECTED)
    risk_level = Column(SAEnum(RiskLevel), nullable=True)
    priority = Column(SAEnum(Priority), nullable=True)
    source_event_id = Column(String, nullable=True)

    # Diagnosis fields
    root_cause = Column(String, nullable=True)
    root_cause_detail = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)  # 0.0 - 1.0

    # Strategy fields
    recommended_strategy = Column(String, nullable=True)
    strategy_data = Column(JSON, nullable=True)

    # Guardian fields
    guardian_status = Column(String, nullable=True)  # APPROVED / BLOCKED / HUMAN_APPROVAL_REQUIRED
    guardian_reason = Column(Text, nullable=True)

    # Execution
    escalation_level = Column(String, nullable=True, default="LEVEL_0")
    retry_count = Column(Float, nullable=True, default=0)
    message_count = Column(Float, nullable=True, default=0)

    # Recovery
    recovered_amount = Column(Float, nullable=True, default=0.0)
    recovery_verified = Column(String, nullable=True)  # VERIFIED_SUCCESS / VERIFIED_FAILURE / UNKNOWN

    # Metadata
    stop_reason = Column(String, nullable=True)
    extra_data = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    closed_at = Column(DateTime(timezone=True), nullable=True)
