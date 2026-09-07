"""
Auto-seed demo data for Vercel serverless cold starts.

Populates the /tmp/ SQLite database with realistic recovery cases, diagnoses,
strategies, guardian decisions, actions, and audit trail entries so the
application shows meaningful data immediately.
"""
import uuid
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Demo case definitions — diverse scenarios in various states
DEMO_CASES = [
    {
        "case_type": "PAYMENT_FAILURE",
        "amount": 30000.0,
        "status": "RECOVERED",
        "recovered": 30000.0,
        "risk_level": "MEDIUM",
        "priority": "HIGH",
        "root_cause": "Insufficient funds on customer card",
        "strategy": "RETRY_PAYMENT",
        "confidence": 0.92,
        "guardian_status": "APPROVED",
        "guardian_reason": "All safety checks passed",
        "hours_ago": 2,
    },
    {
        "case_type": "CHECKOUT_ABANDONMENT",
        "amount": 7500.0,
        "status": "RECOVERED",
        "recovered": 7500.0,
        "risk_level": "LOW",
        "priority": "MEDIUM",
        "root_cause": "Cart abandoned after payment page load failure",
        "strategy": "SEND_RECOVERY_LINK",
        "confidence": 0.85,
        "guardian_status": "APPROVED",
        "guardian_reason": "Message limit not exceeded",
        "hours_ago": 5,
    },
    {
        "case_type": "PAYMENT_FAILURE",
        "amount": 15000.0,
        "status": "BLOCKED",
        "recovered": 0.0,
        "risk_level": "MEDIUM",
        "priority": "HIGH",
        "root_cause": "Card network timeout",
        "strategy": "RETRY_PAYMENT",
        "confidence": 0.78,
        "guardian_status": "BLOCKED",
        "guardian_reason": "Max retry limit (2/2) already reached",
        "retry_count": 2,
        "hours_ago": 3,
    },
    {
        "case_type": "OVERDUE_RECEIVABLE",
        "amount": 250000.0,
        "status": "ESCALATED",
        "recovered": 0.0,
        "risk_level": "CRITICAL",
        "priority": "HIGH",
        "root_cause": "Invoice 25 days overdue — customer unresponsive",
        "strategy": "ESCALATE_TO_HUMAN",
        "confidence": 0.88,
        "guardian_status": "HUMAN_APPROVAL_REQUIRED",
        "guardian_reason": "High-value case (₹2,50,000) requires human approval",
        "hours_ago": 8,
    },
    {
        "case_type": "PAYMENT_FAILURE",
        "amount": 50000.0,
        "status": "RECOVERED",
        "recovered": 50000.0,
        "risk_level": "HIGH",
        "priority": "HIGH",
        "root_cause": "Promise-to-pay broken — customer missed deadline",
        "strategy": "RETRY_PAYMENT",
        "confidence": 0.90,
        "guardian_status": "APPROVED",
        "guardian_reason": "Retry count within limits",
        "hours_ago": 12,
    },
    {
        "case_type": "PAYMENT_FAILURE",
        "amount": 45000.0,
        "status": "ESCALATED",
        "recovered": 0.0,
        "risk_level": "HIGH",
        "priority": "HIGH",
        "root_cause": "AI provider returned low-confidence result",
        "strategy": "ESCALATE_TO_HUMAN",
        "confidence": 0.35,
        "guardian_status": "HUMAN_APPROVAL_REQUIRED",
        "guardian_reason": "AI confidence (35%) below minimum threshold (60%)",
        "hours_ago": 6,
    },
    {
        "case_type": "SUBSCRIPTION_FAILURE",
        "amount": 12000.0,
        "status": "RECOVERED",
        "recovered": 12000.0,
        "risk_level": "MEDIUM",
        "priority": "HIGH",
        "root_cause": "Subscription renewal charge declined",
        "strategy": "RETRY_PAYMENT",
        "confidence": 0.87,
        "guardian_status": "APPROVED",
        "guardian_reason": "All safety checks passed",
        "hours_ago": 1,
    },
    {
        "case_type": "CHECKOUT_ABANDONMENT",
        "amount": 3200.0,
        "status": "CLOSED",
        "recovered": 3200.0,
        "risk_level": "LOW",
        "priority": "MEDIUM",
        "root_cause": "Session expired during payment",
        "strategy": "SEND_RECOVERY_LINK",
        "confidence": 0.82,
        "guardian_status": "APPROVED",
        "guardian_reason": "Communication limits within bounds",
        "hours_ago": 24,
    },
    {
        "case_type": "PAYMENT_FAILURE",
        "amount": 88000.0,
        "status": "DIAGNOSED",
        "recovered": 0.0,
        "risk_level": "HIGH",
        "priority": "HIGH",
        "root_cause": "Bank server downtime during transaction",
        "strategy": None,
        "confidence": 0.75,
        "guardian_status": None,
        "guardian_reason": None,
        "hours_ago": 0.5,
    },
    {
        "case_type": "OVERDUE_RECEIVABLE",
        "amount": 175000.0,
        "status": "STRATEGY_SELECTED",
        "recovered": 0.0,
        "risk_level": "CRITICAL",
        "priority": "HIGH",
        "root_cause": "Large invoice 15 days overdue",
        "strategy": "SEND_REMINDER",
        "confidence": 0.70,
        "guardian_status": None,
        "guardian_reason": None,
        "hours_ago": 4,
    },
    {
        "case_type": "PAYMENT_FAILURE",
        "amount": 5500.0,
        "status": "DETECTED",
        "recovered": 0.0,
        "risk_level": "LOW",
        "priority": "MEDIUM",
        "root_cause": None,
        "strategy": None,
        "confidence": None,
        "guardian_status": None,
        "guardian_reason": None,
        "hours_ago": 0.2,
    },
    {
        "case_type": "SUBSCRIPTION_FAILURE",
        "amount": 24000.0,
        "status": "STOPPED",
        "recovered": 0.0,
        "risk_level": "MEDIUM",
        "priority": "HIGH",
        "root_cause": "Customer explicitly cancelled subscription",
        "strategy": "NO_ACTION",
        "confidence": 0.95,
        "guardian_status": "BLOCKED",
        "guardian_reason": "Stopping rule: customer explicitly opted out",
        "hours_ago": 48,
    },
]


def seed_demo_data(db: Session):
    """Seed the database with demo cases and related records if empty."""
    from app.models.cases import RecoveryCase
    from app.models.recovery import Diagnosis, Strategy, RecoveryAction, GuardianDecision, Escalation
    from app.models.audit import CaseAuditEvent
    from app.models.business import BatchRun

    # Skip if data already exists
    existing = db.query(RecoveryCase).count()
    if existing > 0:
        logger.debug(f"Database already has {existing} cases, skipping seed")
        return

    logger.info("Seeding database with demo data...")
    now = datetime.now(timezone.utc)

    for demo in DEMO_CASES:
        case_id = f"DEMO-{str(uuid.uuid4())[:8].upper()}"
        created_at = now - timedelta(hours=demo["hours_ago"])

        case = RecoveryCase(
            id=str(uuid.uuid4()),
            case_id=case_id,
            merchant_id="DEMO_MERCHANT",
            customer_id=f"CUST-{str(uuid.uuid4())[:6].upper()}",
            case_type=demo["case_type"],
            reference_id=f"REF-{str(uuid.uuid4())[:6].upper()}",
            amount_at_risk=demo["amount"],
            currency="INR",
            status=demo["status"],
            risk_level=demo["risk_level"],
            priority=demo["priority"],
            retry_count=demo.get("retry_count", 0),
            message_count=0,
            confidence=demo["confidence"],
            root_cause=demo.get("root_cause"),
            recommended_strategy=demo.get("strategy"),
            recovered_amount=demo["recovered"],
            guardian_status=demo.get("guardian_status"),
            guardian_reason=demo.get("guardian_reason"),
            recovery_verified="VERIFIED" if demo["recovered"] > 0 else "UNVERIFIED",
            extra_data={},
            created_at=created_at,
        )
        db.add(case)

        # Add diagnosis if case is past DETECTED
        if demo["status"] != "DETECTED" and demo.get("root_cause"):
            diagnosis = Diagnosis(
                id=str(uuid.uuid4()),
                case_id=case_id,
                root_cause=demo["root_cause"],
                confidence=demo.get("confidence", 0.8),
                details=f"Automated diagnosis for {demo['case_type'].replace('_', ' ').lower()}",
                ai_model="llama-3.3-70b-versatile",
                provider="mock",
                created_at=created_at + timedelta(seconds=2),
            )
            db.add(diagnosis)

        # Add strategy if selected
        if demo.get("strategy"):
            strategy_map = {
                "RETRY_PAYMENT": ("Retry Payment", "Attempt payment retry with updated card details", 0.75, 50),
                "SEND_RECOVERY_LINK": ("Send Recovery Link", "Email customer a secure payment link", 0.65, 20),
                "SEND_REMINDER": ("Send Reminder", "Send payment reminder notification", 0.55, 10),
                "ESCALATE_TO_HUMAN": ("Escalate to Human", "Forward to human agent for review", 0.40, 100),
                "NO_ACTION": ("No Action", "Do not take any action", 0.0, 0),
            }
            s_info = strategy_map.get(demo["strategy"], ("Unknown", "Unknown strategy", 0.5, 50))
            strategy = Strategy(
                id=str(uuid.uuid4()),
                case_id=case_id,
                strategy_name=demo["strategy"],
                strategy_label=s_info[0],
                description=s_info[1],
                recovery_probability=s_info[2],
                operational_cost=s_info[3],
                discount_amount=0.0,
                expected_net_recovery=round(demo["amount"] * s_info[2] - s_info[3], 2),
                rank=1,
                is_selected="YES",
                ai_explanation=f"Selected {s_info[0]} as optimal recovery strategy",
                risk_notes="Standard risk assessment applied",
                created_at=created_at + timedelta(seconds=4),
            )
            db.add(strategy)

        # Add guardian decision
        if demo.get("guardian_status"):
            gd = GuardianDecision(
                id=str(uuid.uuid4()),
                case_id=case_id,
                proposed_action=demo.get("strategy", "UNKNOWN"),
                decision=demo["guardian_status"],
                reason=demo["guardian_reason"],
                checks_passed=["retry_limit", "message_limit", "contact_frequency"] if demo["guardian_status"] == "APPROVED" else ["message_limit"],
                checks_failed=[] if demo["guardian_status"] == "APPROVED" else (
                    ["retry_limit"] if demo["guardian_status"] == "BLOCKED" else ["high_value_threshold"]
                ),
                decided_by="POLICY_GUARDIAN",
                created_at=created_at + timedelta(seconds=6),
            )
            db.add(gd)

        # Add recovery action for recovered/closed cases
        if demo["recovered"] > 0:
            action = RecoveryAction(
                id=str(uuid.uuid4()),
                case_id=case_id,
                action_type=demo.get("strategy", "RETRY_PAYMENT"),
                status="VERIFIED_SUCCESS",
                idempotency_key=f"idemp_{case_id}_{str(uuid.uuid4())[:8]}",
                provider_response={"status": "success", "amount": demo["recovered"]},
                amount_recovered=demo["recovered"],
                created_at=created_at + timedelta(seconds=8),
            )
            db.add(action)

        # Add escalation for escalated cases
        if demo["status"] == "ESCALATED":
            escalation = Escalation(
                id=str(uuid.uuid4()),
                case_id=case_id,
                level=5,
                level_name="LEVEL_5_HUMAN_REVIEW",
                reason=demo.get("guardian_reason", "Requires human review"),
                escalated_to="HUMAN_AGENT",
                status="OPEN",
                created_at=created_at + timedelta(seconds=10),
            )
            db.add(escalation)

        # Add audit trail entry
        audit = CaseAuditEvent(
            id=str(uuid.uuid4()),
            case_id=case_id,
            event_type="STATE_CHANGE",
            previous_state="DETECTED",
            new_state=demo["status"],
            actor_type="SYSTEM",
            actor_id="RECOVERY_ENGINE",
            reason=f"Auto-processed: {demo['case_type'].replace('_', ' ').lower()}",
            created_at=created_at + timedelta(seconds=1),
        )
        db.add(audit)

    # Add a batch run record
    batch = BatchRun(
        id=str(uuid.uuid4()),
        batch_id=f"BATCH-{str(uuid.uuid4())[:8].upper()}",
        status="COMPLETED",
        total_cases=len(DEMO_CASES),
        processed_cases=len(DEMO_CASES),
        total_revenue_at_risk=sum(d["amount"] for d in DEMO_CASES),
        total_recovered=sum(d["recovered"] for d in DEMO_CASES),
        recovery_rate=round(
            sum(d["recovered"] for d in DEMO_CASES)
            / sum(d["amount"] for d in DEMO_CASES) * 100, 1
        ),
        cases_recovered=sum(1 for d in DEMO_CASES if d["recovered"] > 0),
        cases_failed=0,
        cases_blocked=sum(1 for d in DEMO_CASES if d["status"] == "BLOCKED"),
        cases_escalated=sum(1 for d in DEMO_CASES if d["status"] == "ESCALATED"),
        cases_stopped=sum(1 for d in DEMO_CASES if d["status"] == "STOPPED"),
        actions_executed=sum(1 for d in DEMO_CASES if d["recovered"] > 0),
        actions_blocked=sum(1 for d in DEMO_CASES if d["status"] == "BLOCKED"),
        human_escalations=sum(1 for d in DEMO_CASES if d["status"] == "ESCALATED"),
        breakdown_by_type={
            ct: {
                "count": sum(1 for d in DEMO_CASES if d["case_type"] == ct),
                "recovered": sum(d["recovered"] for d in DEMO_CASES if d["case_type"] == ct),
            }
            for ct in set(d["case_type"] for d in DEMO_CASES)
        },
        started_at=now - timedelta(hours=1),
        completed_at=now - timedelta(minutes=55),
        created_at=now - timedelta(hours=1),
    )
    db.add(batch)

    db.commit()
    logger.info(f"Seeded {len(DEMO_CASES)} demo cases successfully")
