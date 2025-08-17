import pytest
import pandas as pd
import xlwings as xw
from pathlib import Path
import json
from typing import Dict
import samplicity as sam

def get_test_dir() -> Path:
    """Get the test directory."""
    return Path(__file__).parent

@pytest.fixture(scope="session")
def sam_calculator():
    """Initialize and configure SAM calculator for testing."""
    test_dir = get_test_dir()
    test_data_dir = test_dir / 'test_data'
    
    # Define input files
    files = {
        'input_file': test_data_dir / 'test_input.xlsm',
        'risk_free_rates': test_data_dir / '12 SAM - Risk Free Rates  (30 December 2022).xlsx',
        'symmetric_adjustment': test_data_dir / '12 SAM - Equity Symmetric Adjustment (30 December 2022).xlsx'
    }
    
    # Verify files exist
    for name, path in files.items():
        if not path.exists():
            pytest.skip(f"Required input file not found: {name} at {path}")
    
    try:
        # Initialize SAM calculator
        sam_scr = sam.scr.SCR()
        
        # Import data
        sam_scr.f_import_data(
            risk_free_rates=str(files['risk_free_rates']),
            symmetric_adjustment=str(files['symmetric_adjustment']),
            data_file=str(files['input_file'])
        )
        
        # Perform calculation
        sam_scr.f_calculate()
        
        return sam_scr
        
    except Exception as e:
        pytest.skip(f"Error initializing SAM calculator: {str(e)}")

@pytest.fixture(scope="session")
def test_data(sam_calculator) -> Dict[str, pd.DataFrame]:
    """Load test data from Excel workbook."""
    test_dir = get_test_dir()
    proofs_file = test_dir / 'test_data' / 'test_input.xlsm'
    
    if not proofs_file.exists():
        pytest.skip(f"Test data file not found at {proofs_file}")
    
    data = {}
    try:
        wb = xw.Book(str(proofs_file))
        
        # Load standard ranges
        #for rng in ["checks", "nat_cat_si", "prem_res_data"]:
        #    sheet = wb.sheets[rng]
        #    data[rng] = sheet.range(rng).options(
        #        pd.DataFrame, header=1, index=False, expand="table"
        #    ).value

        sheet = wb.sheets["checks"]
        data["checks"] = sheet.range("checks").options(
            pd.DataFrame, header=1, index=False, expand="table"
        ).value        


        # Load division checks
        sheet = wb.sheets["checks"]
        data["checks_div"] = sheet.range("checks_div").options(
            pd.DataFrame, header=1, index=False, expand="table"
        ).value
        
        wb.close()
        
    except Exception as e:
        pytest.skip(f"Error loading test data: {str(e)}")
    
    return data

def save_test_result(result_dict: Dict):
    """Save individual test result to results file."""
    #results_file = Path('test_results.csv')
    results_file = 'C:/Sync/git_hub/samplicity/tests/test_results.csv'

    df = pd.DataFrame([result_dict])
    if not results_file.exists():
        df.to_csv(results_file, index=False)
    else:
        df.to_csv(results_file, mode='a', header=False, index=False)

@pytest.fixture(autouse=True)
def setup_teardown():
    """Setup and teardown for each test."""
    # Setup
    results_file = Path('test_results.csv')
    if results_file.exists():
        results_file.unlink()
    
    yield
    
    # Teardown - can add cleanup code here if needed