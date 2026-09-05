import pytest
from app.simulation.counterfactual import (
    calculate_single_strategy_net,
    simulate_counterfactuals,
)

def test_counterfactual_strategy_expected_net_value():
    res = calculate_single_strategy_net(
        amount=10000.0,
        recovery_probability=0.80,
        operational_cost=100.0,
        discount_amount=500.0,
    )
    # Expected gross = 0.80 * 10000 = 8000
    # Expected net = 8000 - 100 - 500 = 7400
    assert res["expected_gross_recovery"] == 8000.0
    assert res["expected_net_recovery"] == 7400.0

def test_counterfactual_strategy_ranking_order():
    strategies = [
        {
            "strategy_name": "STRATEGY_A",
            "recovery_probability": 0.50,
            "operational_cost": 50.0,
            "discount_amount": 0.0,
        },
        {
            "strategy_name": "STRATEGY_B",
            "recovery_probability": 0.85,
            "operational_cost": 150.0,
            "discount_amount": 0.0,
        },
        {
            "strategy_name": "STRATEGY_C",
            "recovery_probability": 0.70,
            "operational_cost": 500.0,
            "discount_amount": 1000.0,
        },
    ]
    ranked = simulate_counterfactuals(amount=20000.0, strategies=strategies)
    assert len(ranked) == 3
    # Strategy B should be rank 1 (0.85 * 20000 - 150 = 16850)
    assert ranked[0]["strategy_name"] == "STRATEGY_B"
    assert ranked[0]["rank"] == 1
    assert ranked[0]["is_selected"] == "YES"

def test_counterfactual_zero_amount():
    res = calculate_single_strategy_net(
        amount=0.0,
        recovery_probability=0.80,
        operational_cost=50.0,
        discount_amount=0.0,
    )
    assert res["expected_net_recovery"] == 0.0

def test_counterfactual_negative_net_floors_at_zero():
    res = calculate_single_strategy_net(
        amount=100.0,
        recovery_probability=0.10, # Expected gross = 10
        operational_cost=500.0,    # Cost exceeds gross
        discount_amount=0.0,
    )
    assert res["expected_net_recovery"] == 0.0
