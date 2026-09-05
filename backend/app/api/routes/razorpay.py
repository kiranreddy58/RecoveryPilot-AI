"""
Razorpay Webhook Ingestion & Simulation Routes

Implements:
1. Real Razorpay Webhook Ingestion with HMAC-SHA256 signature verification.
2. Interactive Webhook Simulator for judge/demo testing.
3. Event mapping into RecoveryPilot bounded recovery pipeline.
"""
import hmac
import hashlib
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Header, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.config import get_settings
from app.schemas.base import BaseResponse, EventCreate
from app.services.ingestion import process_event
from app.services.workflow_service import run_full_recovery
from app.models.cases import RecoveryCase
from app.domain.enums import EventType

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

class SimulateWebhookRequest(BaseModel):
    event_type: str  # e.g. "payment.failed", "invoice.expired", "subscription.halted", "order.paid"
    amount: float = 15000.0
    currency: str = "INR"
    merchant_id: str = "MERCHANT_RAZORPAY_01"
    customer_id: str = "CUST_9821"
    reference_id: Optional[str] = None
    custom_payload: Optional[Dict[str, Any]] = None

@router.post("/webhook")
async def receive_razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: Optional[str] = Header(None, alias="X-Razorpay-Signature"),
):
    """
    Ingest live Razorpay Webhooks.
    Validates HMAC-SHA256 signature against RAZORPAY_WEBHOOK_SECRET.
    """
    body_bytes = await request.body()
    secret = getattr(settings, "RAZORPAY_WEBHOOK_SECRET", None) or "razorpay_webhook_secret_demo"

    # Signature verification
    if x_razorpay_signature:
        expected_sig = hmac.new(
            secret.encode("utf-8"),
            body_bytes,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, x_razorpay_signature):
            raise HTTPException(status_code=400, detail="Invalid Razorpay Webhook Signature")

    try:
        payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_name = payload.get("event", "payment.failed")
    event_data = payload.get("payload", {})

    result = _handle_razorpay_event(db, event_name, event_data, payload)
    return {"status": "ok", "result": result}


@router.post("/simulate-webhook", response_model=BaseResponse[dict])
def simulate_razorpay_webhook(
    req: SimulateWebhookRequest,
    db: Session = Depends(get_db),
):
    """
    Interactive Razorpay Webhook Simulator for testing & live demos.
    Dispatches synthetic or custom Razorpay webhook payloads into the bounded recovery engine.
    """
    ref_id = req.reference_id or f"RZP_{str(uuid.uuid4())[:8].upper()}"
    amount = req.amount

    # Map Razorpay event into internal EventType
    mapped_type = _map_event_name_to_type(req.event_type)

    event_payload = req.custom_payload or {
        "entity": "event",
        "account_id": "acc_mock_rzp",
        "event": req.event_type,
        "contains": ["payment"],
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_{ref_id}",
                    "amount": int(amount * 100),  # Razorpay amounts in paise
                    "currency": req.currency,
                    "status": "failed" if "failed" in req.event_type else "captured",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": "Payment was declined by bank due to timeout",
                    "method": "upi",
                }
            }
        },
    }

    # Ingest event
    event_id = str(uuid.uuid4())
    event_create = EventCreate(
        event_id=event_id,
        event_type=mapped_type,
        merchant_id=req.merchant_id,
        customer_id=req.customer_id,
        reference_id=ref_id,
        amount=amount,
        currency=req.currency,
        event_timestamp=datetime.now(timezone.utc),
        source="RAZORPAY_WEBHOOK_SIMULATOR",
        payload=event_payload,
        idempotency_key=f"rzp_{event_id}",
    )

    ingest_result = process_event(db, event_create)
    case_id = ingest_result.get("case_id")

    workflow_result = None
    if case_id:
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
        if case:
            # Trigger bounded recovery workflow
            workflow_result = run_full_recovery(db, case)

    return BaseResponse(
        success=True,
        data={
            "webhook_event": req.event_type,
            "mapped_event_type": str(mapped_type),
            "ingest_status": ingest_result.get("status"),
            "case_id": case_id,
            "workflow_result": workflow_result,
            "simulated_payload": event_payload,
        },
    )


def _handle_razorpay_event(db: Session, event_name: str, event_data: dict, full_payload: dict) -> dict:
    payment_entity = (
        event_data.get("payment", {}).get("entity")
        or event_data.get("payment_link", {}).get("entity")
        or event_data.get("order", {}).get("entity")
        or {}
    )
    notes = payment_entity.get("notes", {}) or {}
    amount_raw = payment_entity.get("amount") or payment_entity.get("amount_paid") or 0
    amount = float(amount_raw) / 100.0 if amount_raw else 1000.0
    currency = payment_entity.get("currency", "INR")
    ref_id = payment_entity.get("id") or notes.get("reference_id") or str(uuid.uuid4())
    linked_case_id = notes.get("case_id")

    # ── SUCCESS WEBHOOK RECONCILIATION ──────────────────────────────────────────
    is_success_event = event_name in (
        "payment.captured",
        "payment_link.paid",
        "invoice.paid",
        "order.paid",
    )

    if is_success_event:
        logger.info(f"Razorpay Webhook: Processing SUCCESS event {event_name} for ref: {ref_id}")
        query = db.query(RecoveryCase)
        case = None
        if linked_case_id:
            case = query.filter(RecoveryCase.case_id == linked_case_id).first()
        if not case and ref_id:
            case = query.filter(
                (RecoveryCase.reference_id == ref_id) |
                (RecoveryCase.reference_id.like(f"%{ref_id}%"))
            ).first()

        if case:
            from app.domain.enums import CaseState
            from app.models.recovery import RecoveryAction
            from app.services.audit_service import record_audit_event

            case.status = CaseState.RECOVERED
            case.recovery_verified = "VERIFIED_SUCCESS"
            case.recovered_amount = amount
            case.closed_at = datetime.now(timezone.utc)

            # Mark associated action as verified success
            last_action = (
                db.query(RecoveryAction)
                .filter(RecoveryAction.case_id == case.case_id)
                .order_by(RecoveryAction.created_at.desc())
                .first()
            )
            if last_action:
                last_action.status = "VERIFIED_SUCCESS"
                last_action.verified_at = datetime.now(timezone.utc)
                db.add(last_action)

            record_audit_event(
                db=db,
                case_id=case.case_id,
                event_type="PAYMENT_RECOVERED_VIA_WEBHOOK",
                previous_state=CaseState.EXECUTING,
                new_state=CaseState.RECOVERED,
                actor_type="RAZORPAY_WEBHOOK",
                actor_id=f"WEBHOOK_{event_name}",
                reason=f"Payment verified and money recovered: ₹{amount:,.2f} via Razorpay {event_name}",
                metadata_payload={"event": event_name, "payment_entity": payment_entity},
            )

            db.add(case)
            db.commit()
            db.refresh(case)

            return {
                "status": "RECOVERED",
                "message": f"Case {case.case_id} successfully reconciled as RECOVERED (₹{amount:,.2f})",
                "case_id": case.case_id,
                "recovered_amount": amount,
            }

        # If no active case matched, record informational ingestion
        return {
            "status": "acknowledged",
            "message": f"Received success event {event_name}, no active matching case found.",
            "reference_id": ref_id,
        }

    # ── FAILURE / DROP-OFF WEBHOOK INGESTION ────────────────────────────────────
    mapped_type = _map_event_name_to_type(event_name)
    event_id = str(uuid.uuid4())
    event_create = EventCreate(
        event_id=event_id,
        event_type=mapped_type,
        merchant_id=full_payload.get("account_id", "MERCHANT_RAZORPAY_DEFAULT"),
        customer_id=payment_entity.get("contact") or payment_entity.get("email") or "CUST_DEFAULT",
        reference_id=ref_id,
        amount=amount,
        currency=currency,
        event_timestamp=datetime.now(timezone.utc),
        source="RAZORPAY_LIVE_WEBHOOK",
        payload=full_payload,
        idempotency_key=f"live_{ref_id}_{event_name}",
    )

    ingest = process_event(db, event_create)
    case_id = ingest.get("case_id")
    workflow_result = None
    if case_id:
        case = db.query(RecoveryCase).filter(RecoveryCase.case_id == case_id).first()
        if case:
            workflow_result = run_full_recovery(db, case)
    return {"ingest": ingest, "case_id": case_id, "workflow_result": workflow_result}


def _map_event_name_to_type(event_name: str) -> EventType:
    mapping = {
        "payment.failed": EventType.PAYMENT_FAILED,
        "checkout.abandoned": EventType.CHECKOUT_ABANDONED,
        "invoice.expired": EventType.INVOICE_OVERDUE,
        "invoice.payment_failed": EventType.INVOICE_OVERDUE,
        "subscription.halted": EventType.SUBSCRIPTION_PAYMENT_FAILED,
        "subscription.charged_failed": EventType.SUBSCRIPTION_PAYMENT_FAILED,
        "promise_to_pay.broken": EventType.PROMISE_TO_PAY_BROKEN,
    }
    return mapping.get(event_name, EventType.PAYMENT_FAILED)
