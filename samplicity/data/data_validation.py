import pandas as pd

# A blank list of all the data conversions that we need to make
#data_converions=[]

# A function to convert None to 0.0

from .data_models import convert_none_to_value, division_detail, counterparty, asset_shocks, asset_data, reinsurance, reinsurance_share, prem_res, nat_cat_si
from pydantic import ValidationError
import logging

# We create a dictionary of all the vlaidatiosn that we need to process
# The name should match up to the name of the imported variable

def validate_data(data_dict):

    # The different data validations that we need to perform
    validations = {
        'division_detail': division_detail,
        'counterparty': counterparty,
        'asset_shocks': asset_shocks,
        'asset_data': asset_data,
        'ri_contract': reinsurance,
        'ri_contract_share': reinsurance_share,
        'prem_res': prem_res,
        'nat_cat_si': nat_cat_si
    }

    # A list of all the dta conversions we ahve performed
    data_conversions=[]

    # A list of all the failed records
    failed_records = []   

    for key, val in validations.items():

        # Convert dataframe to a list of dictionaries
        df=data_dict[key]
        list=df.to_dict(orient='records')

        
        successful_records = []

        for i, record in enumerate(list):
            #division_detail.set_current_row(i)  # Set the current row before validation
            try:
                # We need to re-create the dataframe as we are making data edits
                validated_record = val.model_validate(record,context={'record_id': i, 'data_conversions': data_conversions})
                # Populate the dictionary again
            except ValidationError as e:
                #print(e)
                failed_records.append({'table': key, 'row_no': i, 'data': str(record), 'error':e})
                logging.error(f"Validation error in table {key} in record {i}: {e}")
            else:
                successful_records.append(validated_record.model_dump())

        data_dict[key]=pd.DataFrame(successful_records)
    


    val_errors=pd.DataFrame(failed_records)
    data_dict['validation_errors']=val_errors

    data_conversions=pd.DataFrame(data_conversions)
    data_dict['data_conversions']=data_conversions

    return data_dict