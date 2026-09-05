"""
Stopping Rules Engine — Deterministic

When to stop automation completely and escalate to human.
These are NOT AI decisions. They are hard policy rules.
"""
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class StoppingDecision:
    should_stop: bool
    reason: Optional[str] = None
    escalate_to_human: bool = False
    stop_code: Optional[str] = None


def check_stopping_rules(case_context: dict, policies: dict = None) -> StoppingDecision:
    """
    Check if automation must stop.
    
    Returns StoppingDecision. If should_stop=True, no more automation.
    """
    from app.guardian.policy_guardian import DEFAULT_POLICIES
    p = {**DEFAULT_POLICIES, **(policies or {})}

    retry_count = int(case_context.get("retry_count") or 0)
    message_count = int(case_context.get("message_count") or 0)
    customer_opted_out = bool(case_context.get("customer_opted_out", False))
    ai_confidence = float(case_context.get("confidence") or 1.0)
    guardian_status = case_context.get("guardian_status", "")
    consecutive_failures = int(case_context.get("consecutive_failures") or 0)

    # STOP: Max retries
    if retry_count >= p["MAX_PAYMENT_RETRIES"]:
        return StoppingDecision(
            should_stop=True,
            reason=f"Maximum payment retries ({p['MAX_PAYMENT_RETRIES']}) reached.",
            escalate_to_human=True,
            stop_code="MAX_RETRIES_REACHED",
        )

    # STOP: Max messages
    if message_count >= p["MAX_MESSAGES"]:
        return StoppingDecision(
            should_stop=True,
            reason=f"Maximum communication limit ({p['MAX_MESSAGES']}) reached. Must stop automation.",
            escalate_to_human=True,
            stop_code="MAX_MESSAGES_REACHED",
        )

    # STOP: Customer opted out
    if customer_opted_out:
        return StoppingDecision(
            should_stop=True,
            reason="Customer has opted out. All automation must stop immediately.",
            escalate_to_human=False,
            stop_code="CUSTOMER_OPT_OUT",
        )

    # STOP: Guardian blocked
    if guardian_status == "BLOCKED":
        return StoppingDecision(
            should_stop=True,
            reason="Policy Guardian has blocked all recovery actions.",
            escalate_to_human=True,
            stop_code="GUARDIAN_BLOCKED",
        )

    # STOP: Low confidence — require human
    if ai_confidence < p["MIN_AI_CONFIDENCE_FOR_AUTO_ACTION"]:
        return StoppingDecision(
            should_stop=True,
            reason=f"AI confidence ({ai_confidence:.0%}) is too low for autonomous action.",
            escalate_to_human=True,
            stop_code="LOW_AI_CONFIDENCE",
        )

    # STOP: Repeated failures
    if consecutive_failures >= 3:
        return StoppingDecision(
            should_stop=True,
            reason="Three consecutive recovery attempts failed. Escalating to human.",
            escalate_to_human=True,
            stop_code="CONSECUTIVE_FAILURES",
        )

    # STOP: Expiry window
    created_at = case_context.get("created_at")
    if created_at:
        from datetime import datetime, timezone
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except Exception:
                created_at = None
        if created_at:
            now = datetime.now(timezone.utc) if created_at.tzinfo else datetime.utcnow()
            age_days = (now - created_at).total_seconds() / 86400
            if age_days > p.get("MAX_RECOVERY_DAYS", 30):
                return StoppingDecision(
                    should_stop=True,
                    reason=f"Recovery window expired ({age_days:.1f} days > {p.get('MAX_RECOVERY_DAYS', 30)} days max).",
                    escalate_to_human=False,
                    stop_code="RECOVERY_WINDOW_EXPIRED",
                )

    return StoppingDecision(should_stop=False)
