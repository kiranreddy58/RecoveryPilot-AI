import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey

from app.core.database import Base

class CaseAuditEvent(Base):
    __tablename__ = "case_audit_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id = Column(String, ForeignKey("recovery_cases.case_id"), nullable=False, index=True)
    event_type = Column(String, nullable=False)
    previous_state = Column(String, nullable=True)
    new_state = Column(String, nullable=False)
    actor_type = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    metadata_payload = Column(JSON, nullable=True)
    previous_event_hash = Column(String(64), nullable=True)
    current_event_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
