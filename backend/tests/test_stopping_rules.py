import pytest
from app.guardian.stopping_rules import check_stopping_rules

def test_stopping_rules_normal_case():
    context = {
        "retry_count": 0,
        "message_count": 0,
        "confidence": 0.90,
        "guardian_status": "APPROVED",
        "customer_opted_out": False,
    }
    decision = check_stopping_rules(context)
    assert decision.should_stop is False
    assert decision.escalate_to_human is False

def test_stopping_rules_opt_out():
    context = {
        "retry_count": 0,
        "message_count": 0,
        "confidence": 0.90,
        "customer_opted_out": True,
    }
    decision = check_stopping_rules(context)
    assert decision.should_stop is True
    assert "opt" in decision.reason.lower()

def test_stopping_rules_low_confidence():
    context = {
        "retry_count": 0,
        "message_count": 0,
        "confidence": 0.35, # below 0.60
    }
    decision = check_stopping_rules(context)
    assert decision.should_stop is True
    assert decision.escalate_to_human is True
