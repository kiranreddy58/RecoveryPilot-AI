import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, Enum as SAEnum, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base
from app.domain.enums import EventType

class RecoveryEvent(Base):
    __tablename__ = "recovery_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, unique=True, index=True, nullable=False)
    event_type = Column(SAEnum(EventType), nullable=False)
    merchant_id = Column(String, nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)
    reference_id = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    currency = Column(String, nullable=True)
    event_timestamp = Column(DateTime(timezone=True), nullable=False)
    source = Column(String, nullable=True)
    payload = Column(JSON, nullable=True)
    idempotency_key = Column(String, unique=True, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_status = Column(String, nullable=True)
