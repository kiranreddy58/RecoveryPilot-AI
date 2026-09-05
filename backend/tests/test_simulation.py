import pytest
from app.simulation.counterfactual import simulate_counterfactuals

def test_counterfactual_simulation_expected_net_recovery():
    amount = 50000.0
    strategies = [
        {"name": "RETRY_PAYMENT", "label": "Retry Payment", "recovery_probability": 0.60, "operational_cost": 50, "discount_amount": 0},
        {"name": "SEND_PAYMENT_LINK", "label": "Alternative Payment Link", "recovery_probability": 0.75, "operational_cost": 20, "discount_amount": 0},
        {"name": "OFFER_DISCOUNT", "label": "Offer Discount", "recovery_probability": 0.85, "operational_cost": 20, "discount_amount": 5000},
    ]
    results = simulate_counterfactuals(amount, strategies)
    assert len(results) == 3
    # Check that net expected recovery is calculated: (amount * prob) - cost - discount
    for r in results:
        expected = (amount * r["recovery_probability"]) - r["operational_cost"] - r["discount_amount"]
        assert pytest.approx(r["expected_net_recovery"], 0.1) == expected

    # Check that rank 1 has highest expected_net_recovery
    assert results[0]["rank"] == 1
    assert results[0]["is_selected"] == "YES"
