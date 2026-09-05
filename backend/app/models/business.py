import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Text, JSON, Integer, Boolean

from app.core.database import Base


class PromiseToPay(Base):
    """Tracks customer promises to pay."""
    __tablename__ = "promise_to_pay"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, index=True, nullable=True)
    merchant_id = Column(String, nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)
    reference_id = Column(String, nullable=True)          # invoice/order ID
    
    promised_amount = Column(Float, nullable=False)
    currency = Column(String, nullable=True, default="INR")
    promised_date = Column(DateTime(timezone=True), nullable=False)
    
    # PROMISED / DUE_TODAY / KEPT / BROKEN
    status = Column(String, nullable=False, default="PROMISED")
    
    channel = Column(String, nullable=True)               # EMAIL / PHONE / WHATSAPP
    notes = Column(Text, nullable=True)
    
    checked_at = Column(DateTime(timezone=True), nullable=True)
    kept_at = Column(DateTime(timezone=True), nullable=True)
    broken_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Subscription(Base):
    """Merchant subscription records."""
    __tablename__ = "subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    subscription_id = Column(String, unique=True, nullable=False)
    merchant_id = Column(String, nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)
    
    plan_name = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=True, default="INR")
    interval = Column(String, nullable=True, default="MONTHLY")  # WEEKLY / MONTHLY / YEARLY
    
    status = Column(String, nullable=False, default="ACTIVE")  # ACTIVE / PAST_DUE / CANCELLED / PAUSED
    
    successful_payment_count = Column(Integer, nullable=True, default=0)
    failed_payment_count = Column(Integer, nullable=True, default=0)
    last_failed_reason = Column(String, nullable=True)
    retry_count = Column(Integer, nullable=True, default=0)
    
    next_billing_date = Column(DateTime(timezone=True), nullable=True)
    last_payment_date = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class Invoice(Base):
    """B2B invoice for overdue receivable tracking."""
    __tablename__ = "invoices"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    invoice_id = Column(String, unique=True, nullable=False)
    merchant_id = Column(String, nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)
    
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=True, default="INR")
    
    due_date = Column(DateTime(timezone=True), nullable=False)
    issued_date = Column(DateTime(timezone=True), nullable=True)
    
    status = Column(String, nullable=False, default="UNPAID")  # UNPAID / PARTIAL / PAID / OVERDUE / WRITTEN_OFF
    
    days_overdue = Column(Integer, nullable=True, default=0)
    reminder_count = Column(Integer, nullable=True, default=0)
    last_reminder_at = Column(DateTime(timezone=True), nullable=True)
    
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class BatchRun(Base):
    """Tracks a batch processing run."""
    __tablename__ = "batch_runs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    batch_id = Column(String, unique=True, nullable=False)
    
    total_cases = Column(Integer, nullable=True, default=0)
    processed_cases = Column(Integer, nullable=True, default=0)
    status = Column(String, nullable=False, default="PENDING")  # PENDING / RUNNING / COMPLETED / FAILED
    
    # Metrics
    total_revenue_at_risk = Column(Float, nullable=True, default=0.0)
    total_recovered = Column(Float, nullable=True, default=0.0)
    recovery_rate = Column(Float, nullable=True, default=0.0)
    
    cases_recovered = Column(Integer, nullable=True, default=0)
    cases_failed = Column(Integer, nullable=True, default=0)
    cases_blocked = Column(Integer, nullable=True, default=0)
    cases_escalated = Column(Integer, nullable=True, default=0)
    cases_stopped = Column(Integer, nullable=True, default=0)
    actions_executed = Column(Integer, nullable=True, default=0)
    actions_blocked = Column(Integer, nullable=True, default=0)
    human_escalations = Column(Integer, nullable=True, default=0)
    low_confidence_cases = Column(Integer, nullable=True, default=0)
    
    breakdown_by_type = Column(JSON, nullable=True)
    
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
