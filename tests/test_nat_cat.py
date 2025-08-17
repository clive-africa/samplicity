import pytest
import numpy as np
from typing import Dict, Any
from tests.conftest import save_test_result

def verify_result(expected: float, actual: float, threshold: float = 0.01) -> bool:
    """Verify if the actual result matches expected within threshold."""
    if np.isnan(expected) and np.isnan(actual):
        return True
    if np.isnan(expected) or np.isnan(actual):
        return False
    return abs(actual - expected) < threshold

def save_check_result(class_name: str, category: str, division: Any, 
                     expected: float, actual: float, threshold: float = 0.01):
    """Save test result with validation."""
    result = {
        "class": class_name,
        "category": category,
        "division": str(division) if division else None,
        "test_result": float(expected),
        "python_result": float(actual),
        "pass": verify_result(expected, actual, threshold)
    }
    save_test_result(result)
    return result

@pytest.mark.nat_cat
def test_nat_cat_base_charges(sam_calculator, test_data):
    """Test natural catastrophe base charges."""
    nat_cat = sam_calculator.classes["nat_cat"]
    test_categories = ["eq_charge", "hail_charge", "horizontal_10", "horizontal_20"]
    
    for cat in test_categories:
        expected = test_data["checks"].loc[
            test_data["checks"]["charge"] == cat, "value"
        ].iloc[0]
        actual = nat_cat.output[("base", cat)].iloc[-1, 0].astype(float)
        
        result = save_check_result("nat_cat", cat, None, expected, actual)
        assert result["pass"], (
            f"Failed for {cat}: "
            f"expected {result['test_result']:.2f}, "
            f"got {result['python_result']:.2f}"
        )

@pytest.mark.nat_cat
def test_nat_cat_diversification(sam_calculator, test_data):
    """Test natural catastrophe diversification calculations."""
    nat_cat = sam_calculator.classes["nat_cat"]
    test_categories = ["eq_charge", "hail_charge", "horizontal_10", "horizontal_20"]
    checks_col = [col for col in test_data["checks_div"] if col not in ["charge", "base"]]
    
    for cat in test_categories:
        for col in checks_col:
            set_col = frozenset(col.replace(";", ""))
            expected = test_data["checks_div"].loc[
                test_data["checks_div"]["charge"] == cat, col
            ].iloc[0].astype(float).item()
            
            actual = nat_cat.output[("base", cat)].loc[[set_col]]["charge"].iloc[0].astype(float).item()
            
            result = save_check_result("nat_cat", cat, set_col, expected, actual)
            assert result["pass"], (
                f"Failed for {cat} {set_col}: "
                f"expected {result['test_result']:.2f}, "
                f"got {result['python_result']:.2f}"
            )