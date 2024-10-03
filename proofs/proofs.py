# This file will help perform some of the tests that are needed for the different elements of the SAM calculation.


import xlwings as xw
import pandas as pd
from samplicity.nat_cat import NatCat
from samplicity.prem_res import PremRes
from samplicity.factor_cat import FactorCat
import pickle

# sam_scr.f_save_pickle('C:/git_hub/samplicity/.proofs/sam_scr.p')
# Load the pickle file

# pickle_file = 'C:/git_hub/samplicity/.proofs/sam_scr.p'
# with open(pickle_file, 'rb') as f:
#     sam_scr = pickle.load(f)

# The location of our natural catastrophe sum insured information
import_file = "C:/git_hub/samplicity/.proofs/proofs.xlsx"

# Open the workbook (assuming it's already open)
wb = xw.Book(import_file)

## IMPORT ALL OUR RESULTS

data = {}
for rng in ["checks", "nat_cat_si", "prem_res_data"]:
    sheet = wb.sheets[rng]
    data[rng] = (
        sheet.range(rng)
        .options(pd.DataFrame, header=1, index=False, expand="table")
        .value
    )

# All the chesk we perform
checks = data["checks"]

## NATURAL CATASTROPHE RISK

# Now we 'inject' the data into our sam_scr class
# We need to have run the code before
sam_scr.classes["data"].output["data"]["nat_cat_si"] = data["nat_cat_si"]

# Now we calcualte the natural catstrophe catastropeh risk
nat_cat = NatCat(sam_scr, "nat_cat", True)

# print(nat_cat.output.keys())

dat = sam_scr.classes["nat_cat"].output["nat_cat_data"]
tsi = (
    dat[["res_buildings", "comm_buildings", "contents", "engineering", "motor"]]
    .sum()
    .sum()
)


for cat in ["eq_charge", "hail_charge", "horizontal_10", "horizontal_20"]:
    res = checks.loc[checks["charge"] == cat, "value"].iloc[0]
    python_result = nat_cat.output[("base", cat)].iloc[0, 0].astype(float)
    result = abs(python_result - res) < 0.01
    print(f"{cat}: Test Result: {result} - {python_result:.2f} vs {res:.2f}")

## PREMIUM AND RESERVE RISK

# Now we 'inject' the data into our sam_scr class
# We need to have run the code before
sam_scr.classes["data"].output["data"]["prem_res"] = data["prem_res_data"]

# Now we calcualte the natural catstrophe catastropeh risk
prem_res = PremRes(sam_scr, "prem_res", True)

dat = sam_scr.classes["prem_res"].output["gross"]

for chrg in ["premium", "reserve", "overall"]:
    res = checks.loc[checks["charge"] == chrg, "value"].iloc[0]
    python_result = prem_res.output["gross"][chrg].iloc[0].astype(float)
    result = abs(python_result - res) < 0.01
    print(f"{chrg}: Test Result: {result} - {python_result:.2f} vs {res:.2f}")


## FACTOR BASED CAT

# We don't need to import the data as we already have the data in prem_res
factor_cat = FactorCat(sam_scr, "factor_cat", True)
for chrg in factor_cat.output["base"].columns.to_list():
    res = checks.loc[checks["charge"] == chrg, "value"].iloc[0]
    python_result = factor_cat.output["base"][chrg].iloc[0].astype(float)
    result = abs(python_result - res) < 0.01
    print(f"{chrg}: Test Result: {result} - {python_result:.2f} vs {res:.2f}")

self = sam_scr.classes["factor_cat"]
