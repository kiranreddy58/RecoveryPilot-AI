"""
Policy Guardian — Fully Deterministic Safety Layer

Architecture rule:
    AI PROPOSES → GUARDIAN VALIDATES → APPROVE / BLOCK / HUMAN_APPROVAL_REQUIRED → ONLY APPROVED EXECUTES

The Guardian has NO AI. It is pure deterministic Python.
It CANNOT be bypassed by any AI component.
"""
import logging
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# POLICY CONFIGURATION — All policy values are here, never hardcoded elsewhere
# ─────────────────────────────────────────────────────────

DEFAULT_POLICIES = {
    "MAX_PAYMENT_RETRIES": 2,
    "MAX_MESSAGES": 3,
    "MIN_HOURS_BETWEEN_CONTACTS": 24,
    "MAX_RECOVERY_DAYS": 30,
    "MAX_DISCOUNT_PERCENT": 10,
    "HIGH_VALUE_THRESHOLD_INR": 100000,       # ₹1,00,000 requires human approval
    "HIGH_VALUE_THRESHOLD_USD": 2000,
    "MIN_AI_CONFIDENCE_FOR_AUTO_ACTION": 0.60, # Below this → escalate
    "MAX_ESCALATION_LEVEL": 5,
    "LEGAL_NOTICE_REQUIRES_APPROVAL": True,
    "SUBSCRIPTION_MAX_RETRIES": 3,
    "MANDATE_MAX_RETRIES": 3,
}


@dataclass
class GuardianResult:
    """Result of a Policy Guardian check."""
    decision: str          # APPROVED / BLOCKED / HUMAN_APPROVAL_REQUIRED
    reason: str
    checks_passed: list = field(default_factory=list)
    checks_failed: list = field(default_factory=list)
    policy_snapshot: dict = field(default_factory=dict)
    blocking_rule: Optional[str] = None

    @property
    def is_approved(self) -> bool:
        return self.decision == "APPROVED"

    @property
    def is_blocked(self) -> bool:
        return self.decision == "BLOCKED"

    @property
    def requires_human(self) -> bool:
        return self.decision == "HUMAN_APPROVAL_REQUIRED"


class PolicyGuardian:
    """
    Deterministic Policy Guardian.
    
    Validates every proposed action against policy rules.
    AI cannot bypass this — the Guardian is the last line of defense.
    """

    def __init__(self, policies: dict = None):
        self.policies = {**DEFAULT_POLICIES, **(policies or {})}

    def check(
        self,
        proposed_action: str,
        case_context: dict,
        merchant_policies: dict = None,
    ) -> GuardianResult:
        """
        Main entry point. Check if a proposed action is allowed.
        
        Args:
            proposed_action: Action name e.g. "RETRY_PAYMENT", "SEND_PAYMENT_LINK"
            case_context: Dict with case data — retry_count, message_count, amount, etc.
            merchant_policies: Optional merchant-specific policy overrides
            
        Returns:
            GuardianResult with APPROVED / BLOCKED / HUMAN_APPROVAL_REQUIRED
        """
        policies = {**self.policies, **(merchant_policies or {})}
        checks_passed = []
        checks_failed = []

        amount = float(case_context.get("amount_at_risk") or case_context.get("amount") or 0)
        currency = case_context.get("currency", "INR")
        retry_count = int(case_context.get("retry_count") or 0)
        message_count = int(case_context.get("message_count") or 0)
        ai_confidence = float(case_context.get("confidence") or 1.0)
        last_contacted_at = case_context.get("last_contacted_at")  # datetime or None
        created_at = case_context.get("created_at")                # datetime or None
        customer_opted_out = bool(case_context.get("customer_opted_out", False))
        case_type = case_context.get("case_type", "")

        # ─── RULE 1: Customer opt-out ───────────────────────────────────
        if customer_opted_out and proposed_action in (
            "SEND_PAYMENT_LINK", "SEND_REMINDER", "SEND_DISCOUNT_OFFER",
            "SEND_RECOVERY_LINK", "SEND_CARD_UPDATE_LINK",
        ):
            checks_failed.append("CUSTOMER_OPTED_OUT")
            return GuardianResult(
                decision="BLOCKED",
                reason="Customer has opted out of recovery communications.",
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                policy_snapshot=policies,
                blocking_rule="CUSTOMER_OPTED_OUT",
            )
        checks_passed.append("CUSTOMER_OPTED_OUT_CHECK")

        # ─── RULE 2: Max retry limit ─────────────────────────────────────
        if proposed_action in ("RETRY_PAYMENT", "RETRY_MANDATE", "RETRY_BILLING"):
            max_retries = policies["MAX_PAYMENT_RETRIES"]
            if case_type == "SUBSCRIPTION_PAYMENT_FAILED":
                max_retries = policies["SUBSCRIPTION_MAX_RETRIES"]
            elif case_type == "MANDATE_PAYMENT_FAILED":
                max_retries = policies["MANDATE_MAX_RETRIES"]

            if retry_count >= max_retries:
                checks_failed.append("MAX_RETRIES_EXCEEDED")
                return GuardianResult(
                    decision="BLOCKED",
                    reason=f"Maximum retry limit reached ({retry_count}/{max_retries}). No further retries allowed.",
                    checks_passed=checks_passed,
                    checks_failed=checks_failed,
                    policy_snapshot=policies,
                    blocking_rule="MAX_RETRIES_EXCEEDED",
                )
            checks_passed.append("RETRY_LIMIT_CHECK")

        # ─── RULE 3: Max message limit ───────────────────────────────────
        if proposed_action in (
            "SEND_PAYMENT_LINK", "SEND_REMINDER", "SEND_DISCOUNT_OFFER",
            "SEND_RECOVERY_LINK", "SEND_CARD_UPDATE_LINK",
        ):
            if message_count >= policies["MAX_MESSAGES"]:
                checks_failed.append("MAX_MESSAGES_EXCEEDED")
                return GuardianResult(
                    decision="BLOCKED",
                    reason=f"Maximum communication limit reached ({message_count}/{policies['MAX_MESSAGES']}). Automation must stop.",
                    checks_passed=checks_passed,
                    checks_failed=checks_failed,
                    policy_snapshot=policies,
                    blocking_rule="MAX_MESSAGES_EXCEEDED",
                )
            checks_passed.append("MESSAGE_LIMIT_CHECK")

        # ─── RULE 4: Minimum hours between contacts ──────────────────────
        if proposed_action in (
            "SEND_PAYMENT_LINK", "SEND_REMINDER", "SEND_DISCOUNT_OFFER",
            "SEND_RECOVERY_LINK", "SEND_CARD_UPDATE_LINK",
        ) and last_contacted_at:
            if isinstance(last_contacted_at, str):
                from dateutil import parser as dtparser
                last_contacted_at = dtparser.parse(last_contacted_at)
            now = datetime.now(timezone.utc) if last_contacted_at.tzinfo else datetime.utcnow()
            hours_since = (now - last_contacted_at).total_seconds() / 3600
            min_hours = policies["MIN_HOURS_BETWEEN_CONTACTS"]
            if hours_since < min_hours:
                checks_failed.append("CONTACT_FREQUENCY_VIOLATION")
                return GuardianResult(
                    decision="BLOCKED",
                    reason=f"Minimum {min_hours}h between contacts not met. Last contact was {hours_since:.1f}h ago.",
                    checks_passed=checks_passed,
                    checks_failed=checks_failed,
                    policy_snapshot=policies,
                    blocking_rule="CONTACT_FREQUENCY_VIOLATION",
                )
            checks_passed.append("CONTACT_FREQUENCY_CHECK")

        # ─── RULE 5: Recovery window expired ─────────────────────────────
        if created_at:
            if isinstance(created_at, str):
                from dateutil import parser as dtparser
                created_at = dtparser.parse(created_at)
            now = datetime.now(timezone.utc) if created_at.tzinfo else datetime.utcnow()
            days_since = (now - created_at).days
            max_days = policies["MAX_RECOVERY_DAYS"]
            if days_since > max_days and proposed_action != "ESCALATE_TO_HUMAN":
                checks_failed.append("RECOVERY_WINDOW_EXPIRED")
                return GuardianResult(
                    decision="BLOCKED",
                    reason=f"Recovery window of {max_days} days expired. Case is {days_since} days old.",
                    checks_passed=checks_passed,
                    checks_failed=checks_failed,
                    policy_snapshot=policies,
                    blocking_rule="RECOVERY_WINDOW_EXPIRED",
                )
            checks_passed.append("RECOVERY_WINDOW_CHECK")

        # ─── RULE 6: Discount limits ─────────────────────────────────────
        if proposed_action == "SEND_DISCOUNT_OFFER":
            discount_pct = float(case_context.get("discount_percent", 0))
            max_discount = policies["MAX_DISCOUNT_PERCENT"]
            if discount_pct > max_discount:
                checks_failed.append("DISCOUNT_LIMIT_EXCEEDED")
                return GuardianResult(
                    decision="BLOCKED",
                    reason=f"Proposed discount {discount_pct}% exceeds policy maximum of {max_discount}%.",
                    checks_passed=checks_passed,
                    checks_failed=checks_failed,
                    policy_snapshot=policies,
                    blocking_rule="DISCOUNT_LIMIT_EXCEEDED",
                )
            checks_passed.append("DISCOUNT_LIMIT_CHECK")

        # ─── RULE 7: High-value requires human approval ───────────────────
        threshold = policies["HIGH_VALUE_THRESHOLD_INR"] if currency == "INR" else policies["HIGH_VALUE_THRESHOLD_USD"]
        if amount >= threshold and proposed_action not in ("DO_NOTHING", "ESCALATE_TO_HUMAN"):
            checks_failed.append("HIGH_VALUE_REQUIRES_APPROVAL")
            return GuardianResult(
                decision="HUMAN_APPROVAL_REQUIRED",
                reason=f"Transaction amount ₹{amount:,.0f} exceeds high-value threshold of ₹{threshold:,.0f}. Human approval required.",
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                policy_snapshot=policies,
                blocking_rule="HIGH_VALUE_REQUIRES_APPROVAL",
            )
        checks_passed.append("HIGH_VALUE_CHECK")

        # ─── RULE 8: Low AI confidence ────────────────────────────────────
        min_confidence = policies["MIN_AI_CONFIDENCE_FOR_AUTO_ACTION"]
        if ai_confidence < min_confidence and proposed_action not in ("DO_NOTHING", "ESCALATE_TO_HUMAN"):
            checks_failed.append("LOW_AI_CONFIDENCE")
            return GuardianResult(
                decision="HUMAN_APPROVAL_REQUIRED",
                reason=f"AI confidence {ai_confidence:.0%} is below minimum threshold {min_confidence:.0%} for autonomous action.",
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                policy_snapshot=policies,
                blocking_rule="LOW_AI_CONFIDENCE",
            )
        checks_passed.append("AI_CONFIDENCE_CHECK")

        # ─── RULE 9: Legal notice requires approval ───────────────────────
        if proposed_action == "LEGAL_NOTICE" and policies["LEGAL_NOTICE_REQUIRES_APPROVAL"]:
            return GuardianResult(
                decision="HUMAN_APPROVAL_REQUIRED",
                reason="Legal notice actions always require explicit human approval.",
                checks_passed=checks_passed,
                checks_failed=checks_failed,
                policy_snapshot=policies,
                blocking_rule="LEGAL_NOTICE_REQUIRES_APPROVAL",
            )
        checks_passed.append("LEGAL_NOTICE_CHECK")

        # ─── ALL CHECKS PASSED ────────────────────────────────────────────
        return GuardianResult(
            decision="APPROVED",
            reason=f"All {len(checks_passed)} policy checks passed.",
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            policy_snapshot=policies,
        )
