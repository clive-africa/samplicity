# This file will help perform some of the tests that are needed for the different elements of the SAM calculation.


import xlwings as xw
import pandas as pd
from samplicity.nat_cat import NatCat
from samplicity.prem_res import PremRes
from samplicity.factor_cat import FactorCat
from samplicity.op_risk import OpRisk
import pickle

# sam_scr.f_save_pickle('C:/git_hub/samplicity/.proofs/sam_scr.p')
# Load the pickle file

# pickle_file = 'C:/git_hub/samplicity/.proofs/sam_scr.p'
# with open(pickle_file, 'rb') as f:
#     sam_scr = pickle.load(f)

# The location of our natural catastrophe sum insured information
import_file = r"C:\git_hub\samplicity_git\samplicity\proofs\proofs.xlsx"

# Open the workbook (assuming it's already open)
wb = xw.Book(import_file)

# test_results=pd.DataFrame(columns=['class','category','division','test_result','python_result','pass'])
test_results = []

## IMPORT ALL OUR RESULTS

data = {}
for rng in ["checks", "nat_cat_si", "prem_res_data"]:
    sheet = wb.sheets[rng]
    data[rng] = (
        sheet.range(rng)
        .options(pd.DataFrame, header=1, index=False, expand="table")
        .value
    )

sheet = wb.sheets["checks"]
data["checks_div"] = (
    sheet.range("checks_div")
    .options(pd.DataFrame, header=1, index=False, expand="table")
    .value
)

# All the chesk we perform
checks = data["checks"]
checks_div = data["checks_div"]


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


# Check the totals
for cat in ["eq_charge", "hail_charge", "horizontal_10", "horizontal_20"]:
    res = checks.loc[checks["charge"] == cat, "value"].iloc[0]
    python_result = nat_cat.output[("base", cat)].iloc[-1, 0].astype(float)
    result = abs(python_result - res) < 0.01
    test_results.append(
        {
            "class": "nat_cat",
            "category": cat,
            "division": None,
            "test_result": res,
            "python_result": python_result,
            "pass": result,
        }
    )
    # print(f"{cat}: Test Result: {result} - {python_result:.2f} vs {res:.2f}")


# Check the diversification figures
checks_col = [col for col in checks_div if col not in ["charge", "base"]]
for cat in ["eq_charge", "hail_charge", "horizontal_10", "horizontal_20"]:
    for col in checks_col:
        set_col = frozenset(col.replace(";", ""))
        res = (
            checks_div.loc[checks_div["charge"] == cat, col]
            .iloc[0]
            .astype(float)
            .item()
        )
        python_result = (
            nat_cat.output[("base", cat)]
            .loc[[set_col]]["charge"]
            .iloc[0]
            .astype(float)
            .item()
        )
        result = abs(python_result - res) < 0.01
        test_results.append(
            {
                "class": "nat_cat",
                "category": cat,
                "division": set_col,
                "test_result": res,
                "python_result": python_result,
                "pass": result,
            }
        )
        # print(
        #     f"{cat} for {set_col}: Test Result: {result} - {python_result:.2f} vs {res:.2f}"
        # )

## PREMIUM AND RESERVE RISK

# Now we 'inject' the data into our sam_scr class
# We need to have run the code before
sam_scr.classes["data"].output["data"]["prem_res"] = data["prem_res_data"]

# Now we calcualte the natural catstrophe catastropeh risk
prem_res = PremRes(sam_scr, "prem_res", True)

dat = sam_scr.classes["prem_res"].output["gross"]

# Chekc the totals
for chrg in ["premium", "reserve", "overall"]:
    res = checks.loc[checks["charge"] == chrg, "value"].iloc[0]
    python_result = prem_res.output["gross"][chrg].iloc[-1].astype(float)
    result = abs(python_result - res) < 0.01
    test_results.append(
        {
            "class": "prem_res",
            "category": chrg,
            "division": None,
            "test_result": res,
            "python_result": python_result,
            "pass": result,
        }
    )
    # print(f"{chrg}: Test Result: {result} - {python_result:.2f} vs {res:.2f}")

# Checks teh diversification
for cat in ["premium", "reserve", "overall"]:
    for col in checks_col:
        set_col = frozenset(col.replace(";", ""))
        res = (
            checks_div.loc[checks_div["charge"] == cat, col]
            .iloc[0]
            .astype(float)
            .item()
        )
        python_result = prem_res.output["gross"][cat].loc[[set_col]].item()
        result = abs(python_result - res) < 0.01
        test_results.append(
        {
            "class": "prem_res",
            "category": cat,
            "division": set_col,
            "test_result": res,
            "python_result": python_result,
            "pass": result,
        }
        )
        # print(
        #     f"{cat} for {set_col}: Test Result: {result} - {python_result:.2f} vs {res:.2f}"
        # )


## FACTOR BASED CAT

# We don't need to import the data as we already have the data in prem_res
factor_cat = FactorCat(sam_scr, "factor_cat", True)
for chrg in factor_cat.output["base"].columns.to_list():
    res = checks.loc[checks["charge"] == chrg, "value"].iloc[0]
    python_result = factor_cat.output["base"][chrg].iloc[-1]
    result = abs(python_result - res) < 0.01
    test_results.append(
        {
            "class": "factor_cat",
            "category": chrg,
            "division": None,
            "test_result": res,
            "python_result": python_result,
            "pass": result,
        }
        )    
    # print(f"{chrg}: Test Result: {result} - {python_result:.2f} vs {res:.2f}")


for chrg in factor_cat.output["base"].columns.to_list():
    for col in checks_col:
        set_col = frozenset(col.replace(";", ""))
        res = (
            checks_div.loc[checks_div["charge"] == chrg, col]
            .iloc[0]
            .astype(float)
            .item()
        )
        python_result = factor_cat.output["base"][chrg].loc[[set_col]].item()
        result = abs(python_result - res) < 0.01
        test_results.append(
        {
            "class": "factor_cat",
            "category": chrg,
            "division": set_col,
            "test_result": res,
            "python_result": python_result,
            "pass": result,
        }
        )    
        # print(
        #     f"{chrg} for {set_col}: Test Result: {result} - {python_result:.2f} vs {res:.2f}"
        # )



# We don't need to import the data as we already have the data in prem_res
op_risk = OpRisk(sam_scr, "op_risk", True)
for chrg in op_risk.output.keys():
    res = checks.loc[checks["charge"] == f"op_{chrg}", "value"].iloc[0]
    python_result = op_risk.output[chrg].iloc[-1].item()
    result = abs(python_result - res) < 0.01
    test_results.append(
        {
            "class": "op_risk",
            "category": chrg,
            "division": None,
            "test_result": res,
            "python_result": python_result,
            "pass": result,
        }
        )    
    # print(f"{chrg}: Test Result: {result} - {python_result:.2f} vs {res:.2f}")


for chrg in op_risk.output.keys():
    for col in checks_col:
        set_col = frozenset(col.replace(";", ""))
        res = (
            checks_div.loc[checks_div["charge"] == f"op_{chrg}", col]
            .iloc[0]
            .astype(float)
            .item()
        )
        if chrg=='provisions':
            mod_chrg='prov'
        elif chrg=='operational_risk':
            mod_chrg='risk'
        else:
            mod_chrg=chrg
        python_result = op_risk.output[chrg].loc[[set_col]][f"op_{mod_chrg}"].item()
        result = abs(python_result - res) < 0.01
        test_results.append(
        {
            "class": "op_risk",
            "category": chrg,
            "division": set_col,
            "test_result": res,
            "python_result": python_result,
            "pass": result,
        }
        )    
        # print(
        #     f"{chrg} for {set_col}: Test Result: {result} - {python_result:.2f} vs {res:.2f}"
        # )


# Market risk checks
market=sam_scr.classes['market_risk'].output['summary_data']
for chrg in market.columns.to_list():
    res = checks.loc[checks["charge"] == chrg, "value"].iloc[0]
    python_result = market[chrg].iloc[-1]
    result = abs(python_result - res) < 0.01
    test_results.append(
        {
            "class": "market_risk",
            "category": chrg,
            "division": None,
            "test_result": res,
            "python_result": python_result,
            "pass": result,
        }
        )    
    




# Generate the summary of results


df=pd.DataFrame(test_results)
df_grouped=df.groupby(['class'], as_index=False).agg({'pass': ['sum', 'count']})
df_grouped.columns=['class', 'sum','count']
df_grouped['pass_rate']=df_grouped['sum']/df_grouped['count']

df_failed=df[df['pass']==False]

print(f"pass percentage: {df['pass'].sum()/len(df)*100:.2f}%")



self = sam_scr.classes["factor_cat"]
