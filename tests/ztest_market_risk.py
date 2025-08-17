import pytest
from conftest import save_test_result

def test_market_risk_charges(sam_scr, test_data):
    """Test market risk charges."""
    market = sam_scr.classes['market_risk'].output['summary_data']
    
    for charge in market.columns.to_list():
        expected = test_data["checks"].loc[
            test_data["checks"]["charge"] == charge, "value"
        ].iloc[0]
        actual = market[charge].iloc[-1]
        
        result = {
            "class": "market_risk",
            "category": charge,
            "division": None,
            "test_result": expected,
            "python_result": actual,
            "pass": abs(actual - expected) < 0.01
        }
        save_test_result(result)
        assert abs(actual - expected) < 0.01, f"Failed for {charge}: expected {expected}, got {actual}"