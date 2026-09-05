import pytest
from app.guardian.policy_guardian import PolicyGuardian

def test_guardian_approved_action():
    guardian = PolicyGuardian()
    context = {
        "amount_at_risk": 5000,
        "currency": "INR",
        "retry_count": 0,
        "message_count": 0,
        "confidence": 0.85,
    }
    result = guardian.check("SEND_PAYMENT_LINK", context)
    assert result.decision == "APPROVED"
    assert len(result.checks_passed) > 0
    assert len(result.checks_failed) == 0

def test_guardian_blocks_excessive_retries():
    guardian = PolicyGuardian()
    context = {
        "amount_at_risk": 5000,
        "currency": "INR",
        "retry_count": 2, # max is 2
        "message_count": 0,
        "confidence": 0.85,
    }
    result = guardian.check("RETRY_PAYMENT", context)
    assert result.decision == "BLOCKED"
    assert "MAX_RETRIES_EXCEEDED" in result.checks_failed

def test_guardian_blocks_excessive_messages():
    guardian = PolicyGuardian()
    context = {
        "amount_at_risk": 5000,
        "currency": "INR",
        "retry_count": 0,
        "message_count": 3, # max is 3
        "confidence": 0.85,
    }
    result = guardian.check("SEND_REMINDER", context)
    assert result.decision == "BLOCKED"
    assert "MAX_MESSAGES_EXCEEDED" in result.checks_failed

def test_guardian_requires_human_approval_for_high_value():
    guardian = PolicyGuardian()
    context = {
        "amount_at_risk": 250000, # > 100,000 threshold
        "currency": "INR",
        "retry_count": 0,
        "message_count": 0,
        "confidence": 0.85,
    }
    result = guardian.check("OFFER_DISCOUNT", context)
    assert result.decision in ["HUMAN_APPROVAL_REQUIRED", "BLOCKED"]
