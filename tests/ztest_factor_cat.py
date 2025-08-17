import pytest
from samplicity.factor_cat import FactorCat
from conftest import save_test_result

def test_factor_cat_base_charges(sam_scr, test_data):
    """Test factor-based catastrophe base charges."""
    # Calculate factor-based catastrophe risk
    factor_cat = FactorCat(sam_scr, "factor_cat", True)
    
    for charge in factor_cat.output["base"].columns.to_list():
        expected = test_data["checks"].loc[
            test_data["checks"]["charge"] == charge, "value"
        ].iloc[0]
        actual = factor_cat.output["base"][charge].iloc[-1]
        
        result = {
            "class": "factor_cat",
            "category": charge,
            "division": None,
            "test_result": expected,
            "python_result": actual,
            "pass": abs(actual - expected) < 0.01
        }
        save_test_result(result)
        assert abs(actual - expected) < 0.01, f"Failed for {charge}: expected {expected}, got {actual}"

def test_factor_cat_diversification(sam_scr, test_data):
    """Test factor-based catastrophe diversification calculations."""
    factor_cat = FactorCat(sam_scr, "factor_cat", True)
    
    checks_col = [col for col in test_data["checks_div"] if col not in ["charge", "base"]]
    
    for charge in factor_cat.output["base"].columns.to_list():
        for col in checks_col:
            set_col = frozenset(col.replace(";", ""))
            expected = test_data["checks_div"].loc[
                test_data["checks_div"]["charge"] == charge, col
            ].iloc[0].astype(float).item()
            
            actual = factor_cat.output["base"][charge].loc[[set_col]].item()
            
            result = {
                "class": "factor_cat",
                "category": charge,
                "division": str(set_col),
                "test_result": expected,
                "python_result": actual,
                "pass": abs(actual - expected) < 0.01
            }
            save_test_result(result)
            assert abs(actual - expected) < 0.01, f"Failed for {charge} {set_col}: expected {expected}, got {actual}"