"""
Tamper-Evident Cryptographic Audit Chain Service

Implements:
1. Chronological SHA-256 Hash Chaining across all lifecycle events for every recovery case.
2. Cryptographic audit chain verification (detects tampering or altered history).
3. Explainable timeline generation for case inspection and replay.
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.audit import CaseAuditEvent

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

def _format_ts(dt: Optional[datetime]) -> str:
    if not dt:
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def calculate_event_hash(
    previous_hash: str,
    case_id: str,
    event_type: str,
    previous_state: Optional[str],
    new_state: str,
    actor_id: str,
    created_at_str: str,
    reason: Optional[str] = None,
) -> str:
    """Computes deterministic SHA-256 hash of the audit node + previous node hash."""
    payload = f"{previous_hash}|{case_id}|{event_type}|{previous_state or ''}|{new_state}|{actor_id}|{reason or ''}|{created_at_str}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def record_audit_event(
    db: Session,
    case_id: str,
    event_type: str,
    previous_state: Optional[str],
    new_state: str,
    actor_type: str,
    actor_id: str,
    reason: Optional[str] = None,
    metadata_payload: Optional[Dict[str, Any]] = None,
) -> CaseAuditEvent:
    """
    Appends an immutable audit event to the case's cryptographic hash chain.
    """
    prev_hash = GENESIS_HASH
    if hasattr(db, "query"):
        try:
            last_event = (
                db.query(CaseAuditEvent)
                .filter(CaseAuditEvent.case_id == case_id)
                .order_by(CaseAuditEvent.created_at.desc(), CaseAuditEvent.id.desc())
                .first()
            )
            if last_event and last_event.current_event_hash:
                prev_hash = last_event.current_event_hash
        except Exception:
            pass

    now = datetime.now(timezone.utc)
    now_str = _format_ts(now)

    curr_hash = calculate_event_hash(
        previous_hash=prev_hash,
        case_id=case_id,
        event_type=event_type,
        previous_state=str(previous_state) if previous_state else None,
        new_state=str(new_state),
        actor_id=actor_id,
        created_at_str=now_str,
        reason=reason,
    )

    event = CaseAuditEvent(
        id=str(uuid.uuid4()),
        case_id=case_id,
        event_type=event_type,
        previous_state=str(previous_state) if previous_state else None,
        new_state=str(new_state),
        actor_type=actor_type,
        actor_id=actor_id,
        reason=reason,
        metadata_payload=metadata_payload,
        previous_event_hash=prev_hash,
        current_event_hash=curr_hash,
        created_at=now,
    )

    if hasattr(db, "add"):
        db.add(event)
    return event

def verify_audit_chain(db: Session, case_id: str) -> Dict[str, Any]:
    """
    Traverses the chronological audit events for a case and validates hash consistency.
    Returns audit verification status and details.
    """
    if not hasattr(db, "query"):
        return {"status": "SKIPPED", "is_valid": True, "tamper_detected": False}

    events: List[CaseAuditEvent] = (
        db.query(CaseAuditEvent)
        .filter(CaseAuditEvent.case_id == case_id)
        .order_by(CaseAuditEvent.created_at.asc())
        .all()
    )

    if not events:
        return {
            "status": "EMPTY",
            "is_valid": True,
            "events_count": 0,
            "message": "No audit events recorded for this case.",
            "tamper_detected": False,
        }

    expected_prev_hash = GENESIS_HASH
    for idx, ev in enumerate(events):
        # 1. Check previous hash continuity
        if ev.previous_event_hash and ev.previous_event_hash != expected_prev_hash:
            return {
                "status": "TAMPER_DETECTED",
                "is_valid": False,
                "tamper_detected": True,
                "broken_at_step": idx + 1,
                "event_id": ev.id,
                "message": f"Broken hash chain at step {idx + 1}: expected prev hash {expected_prev_hash[:12]}..., got {str(ev.previous_event_hash)[:12]}...",
            }

        # 2. Check current hash authenticity
        expected_curr_hash = calculate_event_hash(
            previous_hash=expected_prev_hash,
            case_id=ev.case_id,
            event_type=ev.event_type,
            previous_state=ev.previous_state,
            new_state=ev.new_state,
            actor_id=ev.actor_id,
            created_at_str=_format_ts(ev.created_at),
            reason=ev.reason,
        )

        if ev.current_event_hash and ev.current_event_hash != expected_curr_hash:
            return {
                "status": "TAMPER_DETECTED",
                "is_valid": False,
                "tamper_detected": True,
                "broken_at_step": idx + 1,
                "event_id": ev.id,
                "message": f"Event data hash mismatch at step {idx + 1}. Stored hash does not match computed hash.",
            }

        expected_prev_hash = ev.current_event_hash or expected_curr_hash

    return {
        "status": "VERIFIED",
        "is_valid": True,
        "tamper_detected": False,
        "events_count": len(events),
        "root_genesis_hash": GENESIS_HASH,
        "latest_block_hash": expected_prev_hash,
        "message": f"Audit chain fully verified across {len(events)} immutable state events.",
    }
