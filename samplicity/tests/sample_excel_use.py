# Should not be needed if the project is correctly opened
import sys

sys.path.append("c:/git_hub/samplicity/samplicity")
sys.path.append("c:/git_hub/samplicity/")

import pandas as pd


import samplicity as sam


# The file where our data is stored
import_file = r"C:\git_hub\samplicity_git\samplicity\input\sam_input_poc.xlsm"
risk_free_rates = (
    r"C:\git_hub\samplicity_git\samplicity\input\12 SAM - Risk Free Rates  (30 December 2022).xlsx"
)
symmetric_adjustment = r"C:\git_hub\samplicity_git\samplicity\input\12 SAM - Equity Symmetric Adjustment (30 December 2022).xlsx"

# Create an instance of the SAM SCR class
sam_scr = sam.scr.SCR()

# Import our data
sam_scr.f_import_data(
    risk_free_rates=risk_free_rates,
    symmetric_adjustment=symmetric_adjustment,
    data_file=import_file,
)

# Chekc to see if any of the data checks failed


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

