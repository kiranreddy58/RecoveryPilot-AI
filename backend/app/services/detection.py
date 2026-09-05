from typing import Tuple, Optional
from app.domain.enums import EventType, CaseType, RiskLevel

def detect_risk(event_type: EventType, amount: Optional[float] = None) -> Tuple[bool, Optional[CaseType], Optional[RiskLevel]]:
    is_risk = False
    case_type = None
    risk_level = RiskLevel.LOW

    if event_type in [EventType.PAYMENT_FAILED, EventType.MANDATE_PAYMENT_FAILED]:
        is_risk = True
        case_type = CaseType.PAYMENT_FAILURE
    elif event_type == EventType.CHECKOUT_ABANDONED:
        is_risk = True
        case_type = CaseType.CHECKOUT_ABANDONMENT
    elif event_type == EventType.INVOICE_OVERDUE:
        is_risk = True
        case_type = CaseType.OVERDUE_RECEIVABLE
    elif event_type == EventType.SUBSCRIPTION_PAYMENT_FAILED:
        is_risk = True
        case_type = CaseType.SUBSCRIPTION_FAILURE
    elif event_type == EventType.PROMISE_TO_PAY_BROKEN:
        is_risk = True
        case_type = CaseType.PROMISE_TO_PAY_BROKEN

    if is_risk and amount is not None:
        if amount < 1000:
            risk_level = RiskLevel.LOW
        elif amount < 5000:
            risk_level = RiskLevel.MEDIUM
        elif amount < 10000:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.CRITICAL

    return is_risk, case_type, risk_level
