# Should not be needed if the project is correctly opened
import sys

dir="C:/Sync/git_hub/samplicity"

sys.path.append(f"{dir}/samplicity")
sys.path.append(f"{dir}/")

import pandas as pd


import samplicity as sam


# The file where our data is stored
import_file = f"{dir}/tests/test_data/test_input.xlsm"
risk_free_rates = f"{dir}/tests/test_data/12 SAM - Risk Free Rates  (30 December 2022).xlsx"
symmetric_adjustment = f"{dir}/tests/test_data/12 SAM - Equity Symmetric Adjustment (30 December 2022).xlsx"

# Create an instance of the SAM SCR class
sam_scr = sam.scr.SCR()

# Import our data
sam_scr.f_import_data(
    risk_free_rates=risk_free_rates,
    symmetric_adjustment=symmetric_adjustment,
    data_file=import_file,
)

# Chekc to see if any of the data checks failed
sam_scr.f_validate_data()

# Peform the actual SCR calculation
sam_scr.f_calculate()

# Calcualte Shapely diversification values
sam_scr.f_shapely()

# Save all the results to a pickle file
sam_scr.f_save_pickle()

# Export our results to the sam Excel file
# sam_scr.f_export_results(import_file)

# We cna also display a log of all the runtime of the different functions
run_times = pd.DataFrame(sam_scr.output_runtimes)
print(f"{sum(run_times['runtime']):.2f} seconds")

print(f"{sam_scr.f_error_count():.0f} errors encountered")

