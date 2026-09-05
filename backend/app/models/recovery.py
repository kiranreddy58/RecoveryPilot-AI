import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, Integer

from app.core.database import Base


class Diagnosis(Base):
    """Stores AI-generated root cause analysis for a recovery case."""
    __tablename__ = "diagnoses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, index=True, nullable=False)
    
    root_cause = Column(String, nullable=False)
    root_cause_category = Column(String, nullable=True)   # e.g. TECHNICAL / FINANCIAL / BEHAVIOURAL
    root_cause_detail = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)  # 0.0 – 1.0
    
    ai_provider = Column(String, nullable=True)           # which provider was used
    ai_model = Column(String, nullable=True)
    raw_ai_response = Column(JSON, nullable=True)
    
    fallback_used = Column(String, nullable=True)         # "deterministic" if AI failed
    input_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Strategy(Base):
    """A single recovery strategy proposed for a case."""
    __tablename__ = "strategies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, index=True, nullable=False)
    
    strategy_name = Column(String, nullable=False)        # e.g. "RETRY_PAYMENT"
    strategy_label = Column(String, nullable=True)        # Human-readable
    description = Column(Text, nullable=True)
    
    # Simulation outputs
    recovery_probability = Column(Float, nullable=True)   # 0.0 – 1.0
    operational_cost = Column(Float, nullable=True, default=0.0)
    discount_amount = Column(Float, nullable=True, default=0.0)
    expected_net_recovery = Column(Float, nullable=True)
    
    rank = Column(Integer, nullable=True)                  # 1 = best
    is_selected = Column(String, nullable=True)            # "YES" / "NO"
    
    ai_explanation = Column(Text, nullable=True)
    risk_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class RecoveryAction(Base):
    """An action that was proposed to be executed."""
    __tablename__ = "recovery_actions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, index=True, nullable=False)
    strategy_id = Column(String, nullable=True)
    
    action_type = Column(String, nullable=False)          # e.g. SEND_PAYMENT_LINK
    action_label = Column(String, nullable=True)
    
    # Guardian decision
    guardian_status = Column(String, nullable=True)       # APPROVED / BLOCKED / HUMAN_APPROVAL_REQUIRED
    guardian_reason = Column(Text, nullable=True)
    guardian_checked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Idempotency
    idempotency_key = Column(String, unique=True, nullable=True)
    
    # Execution
    status = Column(String, nullable=False, default="PENDING")
    # PENDING → EXECUTING → VERIFIED_SUCCESS / VERIFIED_FAILURE / UNKNOWN
    
    executed_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class GuardianDecision(Base):
    """Every Policy Guardian check is stored here."""
    __tablename__ = "guardian_decisions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, index=True, nullable=False)
    action_id = Column(String, nullable=True)
    
    proposed_action = Column(String, nullable=False)
    decision = Column(String, nullable=False)             # APPROVED / BLOCKED / HUMAN_APPROVAL_REQUIRED
    
    checks_passed = Column(JSON, nullable=True)           # list of passed rules
    checks_failed = Column(JSON, nullable=True)           # list of failed rules
    reason = Column(Text, nullable=True)
    
    policy_snapshot = Column(JSON, nullable=True)         # snapshot of policies at decision time
    
    decided_by = Column(String, nullable=True, default="POLICY_GUARDIAN")
    human_approver = Column(String, nullable=True)        # if human approved
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Escalation(Base):
    """Tracks escalation ladder progression for a case."""
    __tablename__ = "escalations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, index=True, nullable=False)
    
    level = Column(Integer, nullable=False, default=0)    # 0-5
    level_name = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    escalated_to = Column(String, nullable=True)          # human agent ID or team
    
    status = Column(String, nullable=True, default="OPEN")  # OPEN / RESOLVED / CLOSED
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)
