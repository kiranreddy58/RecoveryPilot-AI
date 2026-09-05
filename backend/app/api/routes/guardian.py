"""
Policy Guardian Configuration API Routes

Allows real-time inspection and runtime tuning of safety policies:
- Max retry limits
- Max communication limits
- Contact frequency window (hours)
- Recovery validity window (days)
- High-value human approval threshold (INR)
- AI confidence threshold for auto-action
- Max discount limit (%)
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.guardian.policy_guardian import DEFAULT_POLICIES
from app.models.policy import PolicyConfig
from app.schemas.base import BaseResponse

router = APIRouter()

def get_persisted_policies(db: Session) -> Dict[str, Any]:
    """Retrieve policies from SQLite database with fallback to DEFAULT_POLICIES."""
    policies = {**DEFAULT_POLICIES}
    try:
        records = db.query(PolicyConfig).all()
        for rec in records:
            if rec.policy_name in policies:
                # Convert back to appropriate type (int or float)
                default_val = DEFAULT_POLICIES[rec.policy_name]
                if isinstance(default_val, int):
                    policies[rec.policy_name] = int(rec.current_value)
                else:
                    policies[rec.policy_name] = float(rec.current_value)
    except Exception:
        pass
    return policies

class UpdatePolicyRequest(BaseModel):
    MAX_PAYMENT_RETRIES: int = Field(default=2, ge=0, le=10)
    MAX_MESSAGES: int = Field(default=3, ge=0, le=20)
    MIN_HOURS_BETWEEN_CONTACTS: int = Field(default=24, ge=1, le=168)
    MAX_RECOVERY_DAYS: int = Field(default=30, ge=1, le=365)
    HIGH_VALUE_THRESHOLD_INR: float = Field(default=100000.0, ge=1000.0)
    MIN_AI_CONFIDENCE_FOR_AUTO_ACTION: float = Field(default=0.60, ge=0.1, le=1.0)
    MAX_DISCOUNT_PERCENT: float = Field(default=10.0, ge=0.0, le=50.0)

@router.get("/policies", response_model=BaseResponse[Dict[str, Any]])
def get_current_policies(db: Session = Depends(get_db)):
    """Retrieve currently active safety policies from SQLite persistent storage."""
    active = get_persisted_policies(db)
    return BaseResponse(
        success=True,
        data={
            "active_policies": active,
            "default_policies": DEFAULT_POLICIES,
        },
    )

@router.post("/policies", response_model=BaseResponse[Dict[str, Any]])
def update_policies(req: UpdatePolicyRequest, db: Session = Depends(get_db)):
    """Update and persist safety policies dynamically into SQLite."""
    updates = req.model_dump()
    for name, val in updates.items():
        existing = db.query(PolicyConfig).filter(PolicyConfig.policy_name == name).first()
        if existing:
            existing.current_value = float(val)
            existing.version = (existing.version or 1) + 1
            existing.updated_at = datetime.now(timezone.utc)
            existing.updated_by = "MERCHANT_ADMIN"
            db.add(existing)
        else:
            new_rec = PolicyConfig(
                policy_name=name,
                current_value=float(val),
                default_value=float(DEFAULT_POLICIES.get(name, val)),
                updated_by="MERCHANT_ADMIN",
                version=1,
            )
            db.add(new_rec)
    db.commit()

    active = get_persisted_policies(db)
    return BaseResponse(
        success=True,
        data={
            "message": "Policy Guardian rules persisted successfully to SQLite database",
            "active_policies": active,
        },
    )

@router.post("/policies/reset", response_model=BaseResponse[Dict[str, Any]])
def reset_policies(db: Session = Depends(get_db)):
    """Reset safety policies in database back to default baseline."""
    for name, default_val in DEFAULT_POLICIES.items():
        if not isinstance(default_val, (int, float)):
            continue
        existing = db.query(PolicyConfig).filter(PolicyConfig.policy_name == name).first()
        if existing:
            existing.current_value = float(default_val)
            existing.version = (existing.version or 1) + 1
            existing.updated_at = datetime.now(timezone.utc)
            existing.updated_by = "SYSTEM_RESET"
            db.add(existing)
        else:
            new_rec = PolicyConfig(
                policy_name=name,
                current_value=float(default_val),
                default_value=float(default_val),
                updated_by="SYSTEM_RESET",
                version=1,
            )
            db.add(new_rec)
    db.commit()

    active = get_persisted_policies(db)
    return BaseResponse(
        success=True,
        data={
            "message": "Policies reset to default baseline in database",
            "active_policies": active,
        },
    )
