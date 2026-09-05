"""
Counterfactual Strategy Simulator module

Calculates:
- expected recovery amount = amount * probability
- expected net recovery = max(0, expected recovery - operational cost - discount)
- ranks strategies by expected net value
"""
from typing import List, Dict, Any

def calculate_single_strategy_net(
    amount: float,
    recovery_probability: float,
    operational_cost: float = 0.0,
    discount_amount: float = 0.0,
) -> Dict[str, float]:
    expected_recovery = max(0.0, amount * recovery_probability)
    expected_net = max(0.0, expected_recovery - operational_cost - discount_amount)
    return {
        "expected_gross_recovery": round(expected_recovery, 2),
        "expected_net_recovery": round(expected_net, 2),
        "operational_cost": operational_cost,
        "discount_amount": discount_amount,
    }

def simulate_counterfactuals(amount: float, strategies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    results = []
    for strat in strategies:
        prob = strat.get("recovery_probability", 0.0)
        cost = strat.get("operational_cost", 0.0)
        discount = strat.get("discount_amount", 0.0)
        
        calc = calculate_single_strategy_net(amount, prob, cost, discount)
        
        item = {
            **strat,
            "expected_recovery": calc["expected_gross_recovery"],
            "expected_net_recovery": calc["expected_net_recovery"],
        }
        results.append(item)
        
    # Sort descending by expected net recovery
    results.sort(key=lambda x: x["expected_net_recovery"], reverse=True)
    
    for i, r in enumerate(results):
        r["rank"] = i + 1
        r["is_selected"] = "YES" if i == 0 else "NO"
        
    return results
