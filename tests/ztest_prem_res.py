import pytest
from samplicity.prem_res import PremRes
from conftest import save_test_result

def test_prem_res_base_charges(sam_scr, test_data):
    """Test premium and reserve base charges."""
    # Inject test data
    sam_scr.classes["data"].output["data"]["prem_res"] = test_data["prem_res_data"]
    
    # Calculate premium and reserve risk
    prem_res = PremRes(sam_scr, "prem_res", True)
    
    for charge in ["premium", "reserve", "overall"]:
        expected = test_data["checks"].loc[
            test_data["checks"]["charge"] == charge, "value"
        ].iloc[0]
        actual = prem_res.output["gross"][charge].iloc[-1].astype(float)
        
        result = {
            "class": "prem_res",
            "category": charge,
            "division": None,
            "test_result": expected,
            "python_result": actual,
            "pass": abs(actual - expected) < 0.01
        }
        save_test_result(result)
        assert abs(actual - expected) < 0.01, f"Failed for {charge}: expected {expected}, got {actual}"

def test_prem_res_diversification(sam_scr, test_data):
    """Test premium and reserve diversification calculations."""
    prem_res = PremRes(sam_scr, "prem_res", True)
    
    checks_col = [col for col in test_data["checks_div"] if col not in ["charge", "base"]]
    
    for cat in ["premium", "reserve", "overall"]:
        for col in checks_col:
            set_col = frozenset(col.replace(";", ""))
            expected = test_data["checks_div"].loc[
                test_data["checks_div"]["charge"] == cat, col
            ].iloc[0].astype(float).item()
            
            actual = prem_res.output["gross"][cat].loc[[set_col]].item()
            
            result = {
                "class": "prem_res",
                "category": cat,
                "division": str(set_col),
                "test_result": expected,
                "python_result": actual,
                "pass": abs(actual - expected) < 0.01
            }
            save_test_result(result)
            assert abs(actual - expected) < 0.01, f"Failed for {cat} {set_col}: expected {expected}, got {actual}"