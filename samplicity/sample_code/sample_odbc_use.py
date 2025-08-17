# Should not be needed if the project is correctly opened
import sys
sys.path.append("c:/git_hub/sam_scr/")

import samplicity as sam

# The file where our data is stored
conn_string="DRIVER={SQL Server};SERVER=server_name;DATABASE=database_name;UID=user;PWD=password"
risk_free_rates="c:/git_hub/sam_scr/.input/12 SAM - Risk Free Rates  (30 December 2022).xlsx"
symmetric_adjustment="c:/git_hub/sam_scr/.input/12 SAM - Equity Symmetric Adjustment (30 December 2022).xlsx"

# Not covered here but there should be a process to take a snapshot of the data.
# It would also be good the record the details of the valuation run as
# multiple runs could be down with the same snapshot. Particularly if
# you want to get view for different diversification levels. You should get the
# ID from that process to link to your results. This is the ID which can bene hardcoded here.
process_id=-99

#Create an instance of the SAM SCR class
sam_scr=sam.scr.SCR()

# Import our data
# For an MS Access database you only need to supply the location.
sam_scr.f_import_data(
    risk_free_rates=risk_free_rates,
    symmetric_adjustment=symmetric_adjustment,
    conn_string=conn_string,
    import_table='setting_import',
    export_table='setting_export',
)

# Peform the actual SCR calculation
sam_scr.f_calculate()


# Export our results to the database
# The results we wish to extract are already contained in the class
sam_scr.f_export_results(conn_string=conn_string,process_id=process_id)