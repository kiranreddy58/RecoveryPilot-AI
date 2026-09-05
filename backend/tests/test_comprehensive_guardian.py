import pytest
from datetime import datetime, timezone, timedelta
from app.guardian.policy_guardian import PolicyGuardian, DEFAULT_POLICIES
from app.guardian.stopping_rules import check_stopping_rules

@pytest.fixture
def guardian():
    return PolicyGuardian()

def test_guardian_approve_normal_payment_link(guardian):
    context = {
        "amount_at_risk": 5000.0,
        "currency": "INR",
        "retry_count": 0,
        "message_count": 1,
        "confidence": 0.85,
        "customer_opted_out": False,
    }
    res = guardian.check("SEND_PAYMENT_LINK", context)
    assert res.decision == "APPROVED"
    assert "MESSAGE_LIMIT_CHECK" in res.checks_passed
    assert "AI_CONFIDENCE_CHECK" in res.checks_passed

def test_guardian_block_exceeded_retries(guardian):
    context = {
        "amount_at_risk": 5000.0,
        "currency": "INR",
        "retry_count": 2, # Reached max 2 retries
        "message_count": 0,
        "confidence": 0.90,
    }
    res = guardian.check("RETRY_PAYMENT", context)
    assert res.decision == "BLOCKED"
    assert "MAX_RETRIES_EXCEEDED" in res.checks_failed

def test_guardian_block_exceeded_messages(guardian):
    context = {
        "amount_at_risk": 5000.0,
        "currency": "INR",
        "retry_count": 0,
        "message_count": 3, # Reached max 3 messages
        "confidence": 0.90,
    }
    res = guardian.check("SEND_PAYMENT_LINK", context)
    assert res.decision == "BLOCKED"
    assert "MAX_MESSAGES_EXCEEDED" in res.checks_failed

def test_guardian_escalate_high_value_transaction(guardian):
    context = {
        "amount_at_risk": 250000.0, # Exceeds ₹1,00,000 threshold
        "currency": "INR",
        "retry_count": 0,
        "message_count": 0,
        "confidence": 0.95,
    }
    res = guardian.check("SEND_PAYMENT_LINK", context)
    assert res.decision == "HUMAN_APPROVAL_REQUIRED"
    assert "HIGH_VALUE_REQUIRES_APPROVAL" in res.checks_failed

def test_guardian_escalate_low_ai_confidence(guardian):
    context = {
        "amount_at_risk": 5000.0,
        "currency": "INR",
        "retry_count": 0,
        "message_count": 0,
        "confidence": 0.40, # Below 60% confidence
    }
    res = guardian.check("RETRY_PAYMENT", context)
    assert res.decision == "HUMAN_APPROVAL_REQUIRED"
    assert "LOW_AI_CONFIDENCE" in res.checks_failed

def test_guardian_block_customer_opt_out(guardian):
    context = {
        "amount_at_risk": 5000.0,
        "currency": "INR",
        "retry_count": 0,
        "message_count": 0,
        "confidence": 0.90,
        "customer_opted_out": True,
    }
    res = guardian.check("SEND_PAYMENT_LINK", context)
    assert res.decision == "BLOCKED"
    assert "CUSTOMER_OPTED_OUT" in res.checks_failed

def test_guardian_block_expired_recovery_window(guardian):
    old_time = datetime.now(timezone.utc) - timedelta(days=35) # > 30 days
    context = {
        "amount_at_risk": 5000.0,
        "currency": "INR",
        "retry_count": 0,
        "message_count": 0,
        "confidence": 0.90,
        "created_at": old_time,
    }
    res = guardian.check("SEND_PAYMENT_LINK", context)
    assert res.decision == "BLOCKED"
    assert "RECOVERY_WINDOW_EXPIRED" in res.checks_failed

def test_guardian_custom_merchant_policy_override(guardian):
    custom_policy = {
        "MAX_PAYMENT_RETRIES": 1,
        "HIGH_VALUE_THRESHOLD_INR": 50000.0,
    }
    context = {
        "amount_at_risk": 20000.0,
        "currency": "INR",
        "retry_count": 1,
        "confidence": 0.90,
    }
    res = guardian.check("RETRY_PAYMENT", context, merchant_policies=custom_policy)
    assert res.decision == "BLOCKED"
    assert "MAX_RETRIES_EXCEEDED" in res.checks_failed
