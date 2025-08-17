import pytest
from samplicity.op_risk import OpRisk
from conftest import save_test_result

def test_op_risk_base_charges(sam_scr, test_data):
    """Test operational risk base charges."""
    op_risk = OpRisk(sam_scr, "op_risk", True)
    
    for charge in op_risk.output.keys():
        expected = test_data["checks"].loc[
            test_data["checks"]["charge"] == f"op_{charge}", "value"
        ].iloc[0]
        actual = op_risk.output[charge].iloc[-1].item()
        
        result = {
            "class": "op_risk",
            "category": charge,
            "division": None,
            "test_result": expected,
            "python_result": actual,
            "pass": abs(actual - expected) < 0.01
        }
        save_test_result(result)
        assert abs(actual - expected) < 0.01, f"Failed for {charge}: expected {expected}, got {actual}"

def test_op_risk_diversification(sam_scr, test_data):
    """Test operational risk diversification calculations."""
    op_risk = OpRisk(sam_scr, "op_risk", True)
    
    checks_col = [col for col in test_data["checks_div"] if col not in ["charge", "base"]]
    
    for charge in op_risk.output.keys():
        for col in checks_col:
            set_col = frozenset(col.replace(";", ""))
            expected = test_data["checks_div"].loc[
                test_data["checks_div"]["charge"] == f"op_{charge}", col
            ].iloc[0].astype(float).item()
            
            # Handle different charge naming conventions
            if charge == 'provisions':
                mod_charge = 'prov'
            elif charge == 'operational_risk':
                mod_charge = 'risk'
            else:
                mod_charge = charge
                
            actual = op_risk.output[charge].loc[[set_col]][f"op_{mod_charge}"].item()
            
            result = {
                "class": "op_risk",
                "category": charge,
                "division": str(set_col),
                "test_result": expected,
                "python_result": actual,
                "pass": abs(actual - expected) < 0.01
            }
            save_test_result(result)
            assert abs(actual - expected) < 0.01, f"Failed for {charge} {set_col}: expected {expected}, got {actual}"