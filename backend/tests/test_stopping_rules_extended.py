# pyrefly: ignore [missing-import]
import pytest
from datetime import datetime, timezone, timedelta
from app.guardian.stopping_rules import check_stopping_rules, StoppingDecision

def test_stopping_rules_max_retries():
    context = {"retry_count": 2, "message_count": 0, "confidence": 0.90}
    decision = check_stopping_rules(context)
    assert decision.should_stop is True
    assert "retries" in decision.reason.lower()

def test_stopping_rules_max_messages():
    context = {"retry_count": 0, "message_count": 3, "confidence": 0.90}
    decision = check_stopping_rules(context)
    assert decision.should_stop is True
    assert "communication" in decision.reason.lower() or "message" in decision.reason.lower()

def test_stopping_rules_customer_opt_out():
    context = {"retry_count": 0, "message_count": 0, "confidence": 0.90, "customer_opted_out": True}
    decision = check_stopping_rules(context)
    assert decision.should_stop is True
    assert "opted out" in decision.reason.lower()

def test_stopping_rules_recovery_window_expiry():
    context = {
        "retry_count": 0,
        "message_count": 0,
        "confidence": 0.90,
        "created_at": datetime.now(timezone.utc) - timedelta(days=32),
    }
    decision = check_stopping_rules(context)
    assert decision.should_stop is True
    assert "expired" in decision.reason.lower() or "30 days" in decision.reason.lower()

def test_stopping_rules_consecutive_failures():
    context = {"retry_count": 1, "message_count": 1, "consecutive_failures": 3, "confidence": 0.80}
    decision = check_stopping_rules(context)
    assert decision.should_stop is True
    assert decision.escalate_to_human is True

def test_stopping_rules_healthy_case():
    context = {
        "retry_count": 0,
        "message_count": 0,
        "confidence": 0.85,
        "customer_opted_out": False,
        "consecutive_failures": 0,
    }
    decision = check_stopping_rules(context)
    assert decision.should_stop is False
    assert decision.escalate_to_human is False
