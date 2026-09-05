"""
Policy Guardian Configuration Persistence Model

Stores configurable safety rules (e.g. max retries, max messages, frequency limits)
persistently in SQLite across application reboots.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime
from app.core.database import Base

class PolicyConfig(Base):
    __tablename__ = "policy_configs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    policy_name = Column(String(100), unique=True, index=True, nullable=False)
    current_value = Column(Float, nullable=False)
    default_value = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by = Column(String(100), default="SYSTEM")
    version = Column(Integer, default=1)
