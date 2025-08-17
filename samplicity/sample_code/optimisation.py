'''
    A module used to test soem potential performance enhancements.

'''
import sys
sys.path.append("c:/git_hub/samplicity/")

# Teh pickly file we save, saves having to re-import files
import pickle
import pandas as pd
import samplicity as sam
from samplicity.helper import combins_df_col, allocation_matrix
import time

import numpy as np

#from line_profiler import LineProfiler

# pickle.dump(sam_scr,open(r'C:\\git_hub\sam_scr\\sam_scr.p', "wb"))

sam_scr=pickle.load(open('C:/git_hub/samplicity/sam_scr.p', "rb"))

import time
import itertools





# pr_data=sam_scr.f_data("data", "data", "prem_res")

# # Get the diversification fields
# div_field = sam_scr.f_data("data", "data", "diversification_level").iloc[0]
# calc_level = sam_scr.f_data("data", "data", "calculation_level").iloc[0]

# start = time.perf_counter()
# # Generate a list of unique combinations
# lst = combins_df_col(pr_data, div_field, calc_level)
# df_allocation = pd.DataFrame(lst).apply(pd.Series.value_counts, 1).fillna(0)
# df_allocation.index = lst

# df=allocation_matrix(pr_data, div_field, calc_level)

# end=time.perf_counter()
# elapsed = end - start
# print(f'Time taken: {elapsed:.6f} seconds')


# start = time.perf_counter()
# unique=pr_data[div_field].unique()
# combinations = []
# for r in range(1, len(unique) + 1):
#     combinations.extend(itertools.combinations(unique, r))

# # Create a DataFrame with 0s and 1s
# df = pd.DataFrame([{element: (element in combo) for element in unique} for combo in combinations], index=[frozenset(x) for x in combinations])

# # Convert boolean values to int
# df = df.astype(int)

# end=time.perf_counter()
# elapsed = end - start
# print(f'Time taken: {elapsed:.6f} seconds')

# start = time.perf_counter()

# # Group our data by the diversification field.
# pr_data.loc[
#     :, ["gross_p_last", "gross_p_last_24", "gross_claim", "gross_other"]
# ] = pr_data[
#     ["gross_p_last", "gross_p_last_24", "gross_claim", "gross_other"]
# ].fillna(
#     0
# )
# pr_data["gross_tech_prov"] = pr_data["gross_claim"] + pr_data["gross_other"]

# pr_data = (
#     pr_data[
#         [div_field, "gross_p_last", "gross_p_last_24", "gross_tech_prov"]
#     ]
#     .groupby(by=div_field)
#     .sum()
# )

# # Perform our matrix multiplication to get our
# pr_data = df_allocation[pr_data.index].dot(pr_data)


# # Calculate the growth in excess of 20%
# # we can only perform the calculation now, as the divisional
# # allocation will potentially change the result.
# pr_data["excess_prem_growth"] = (
#     pr_data["gross_p_last"] - 1.2 * pr_data["gross_p_last_24"]
# )

# # We shouldn't have any values that are below zero and
# # remove them at this stage. This will mainly apply to the
# # excess premium growth.
# pr_data[pr_data < 0] = 0

# # Calculate the operational premium risk
# pr_data["op_premium"] = (
#     0.03 * pr_data["gross_p_last"] + 0.03 * pr_data["excess_prem_growth"]
# )
# # Calculate the provisions based on operational risk
# pr_data["op_prov"] = 0.03 * pr_data["gross_tech_prov"]

# # We take the greater of premium and provisions based
# pr_data["op_risk"] = pr_data[["op_premium", "op_prov"]].max(axis=1)

# end=time.perf_counter()
# elapsed = end - start
# print(f'Time taken: {elapsed:.6f} seconds')


#######

# PREMIUM RESERVE RISK

######

output={}

n=0
start=time.perf_counter()
n+=1

# Diversifciation columsn and the method of diversification
div_field = sam_scr.f_data("data", "data", "diversification_level").iloc[0]
calc_level = sam_scr.f_data("data", "data", "calculation_level").iloc[0]

# We will be modifying the dta and it is just easier than always
# working with an item in a dictionary
data = sam_scr.f_data("data", "data", "prem_res")

# We need to perform some data changes, the data changes are done here
# as the steps differ for other areas fo the calculation.
# This allows for easier entry of the data that requires manipulation.
data.loc[data["lob_type"] == "NP", "lob"] = "18b"
data.loc[data["lob_type"] == "FNP", "lob"] = "18e"
data.loc[data["lob_type"] == "O", "lob"] = "18c"
data.loc[data["lob_type"] == "FO", "lob"] = "18f"

data["complete_lob"] = data["lob_type"] + data["lob"]

lob = data[["complete_lob", "lob_type", "lob"]].value_counts()
lob = lob.reset_index()

# Loop thorugh gross and net values to get different reserve measures
corr = sam_scr.f_data("data", "metadata", "corr_prem_res").loc[
    lob["lob"], lob["lob"]
]
corr.index = lob["complete_lob"]
corr.columns = lob["complete_lob"]

# W need to multiple our arrays by the different possible combinations
# of products that we require
# lst=combinations_from_df_column(data, 'division',-1)
#lst = combins_df_col(data, div_field, calc_level)
#df_allocation = pd.DataFrame(lst).apply(pd.Series.value_counts, 1).fillna(0)
#df_allocation.index = lst  # [frozenset(x) for x in lst]

end=time.perf_counter()
elapsed = end - start
print(f'Time taken Step {n}: {elapsed:.6f} seconds')

start=time.perf_counter()
n+=1

df_allocation=allocation_matrix(data, div_field, calc_level)
# We calculate the figures for the gross prmemium and reserve risk
# as well as the actual net prmeium and reserve risk. These figures
# will be added to the maxtrix multiplication as a reisnurer.
# This allows  a single calcualtion will all of the results.

end=time.perf_counter()
elapsed = end - start
print(f'Time taken Step {n}: {elapsed:.6f} seconds')

start=time.perf_counter()
n+=1

prem_res = {}
prem_alloc = {}

base_matrix = pd.DataFrame(
    0, index=lob["complete_lob"], columns=np.unique(data[div_field])
)

for val in ["gross", "net"]:
    for dat in ["p", "p_last", "fp_existing", "fp_future", "claim"]:
        prem_res[(val, dat)] = (
            (data)
            .pivot_table(
                val + "_" + dat, "complete_lob", div_field, aggfunc="sum"
            )
            .fillna(0)
            .combine_first(base_matrix)
        )

# We now need to join the dataset to the reisnurance information

end=time.perf_counter()
elapsed = end - start
print(f'Time taken Step {n}: {elapsed:.6f} seconds')

start=time.perf_counter()
n+=1

ri_contract = sam_scr.f_data("data", "data", "ri_contract")[["ri_share"]]
ri_share = sam_scr.f_data("data", "data", "ri_contract_share")[
    ["reinsurance_id", "counterparty_id", "counterparty_share"]
]

ri_data = pd.merge(
    ri_contract,
    ri_share,
    left_index=True,
    right_on="reinsurance_id",
    how="left",
)

ri_data["ri_contract_counterparty_share"] = (
    ri_data["ri_share"] * ri_data["counterparty_share"]
)

calc_ri = pd.merge(
    data,
    ri_data[
        ["reinsurance_id", "ri_contract_counterparty_share", "counterparty_id"]
    ],
    on="reinsurance_id",
    how="inner",
)
calc_ri.fillna({"ri_contract_counterparty_share":0}, inplace=True)

end=time.perf_counter()
elapsed = end - start
print(f'Time taken Step {n}: {elapsed:.6f} seconds')

start=time.perf_counter()
n+=1

for dat in ["p", "p_last", "fp_existing", "fp_future", "claim"]:
    calc_ri.fillna({f'gross_{dat}': 0}, inplace=True)
    calc_ri["rein_" + dat] = (
        calc_ri["gross_" + dat] * calc_ri["ri_contract_counterparty_share"]
    )
    prem_res[("reinsurance", dat)] = calc_ri.pivot_table(
        "rein_" + dat, "complete_lob", div_field, aggfunc="sum"
    )
    prem_res[("reinsurance", dat)] = (
        prem_res[("reinsurance", dat)].fillna(0).combine_first(base_matrix)
    )
    prem_res[("calc net", dat)] = prem_res[("gross", dat)].sub(
        prem_res[("reinsurance", dat)], fill_value=0
    )

reinsurer_data = calc_ri[
    [
        div_field,
        "complete_lob",
        "counterparty_id",
        "rein_p",
        "rein_p_last",
        "rein_fp_existing",
        "rein_fp_future",
        "rein_claim",
    ]
]
reinsurer_data = reinsurer_data.groupby(
    ["counterparty_id", "complete_lob", div_field], as_index=False
).sum()
calc_list = np.unique(reinsurer_data.counterparty_id)
for rein in calc_list:
    data = reinsurer_data[reinsurer_data["counterparty_id"] == rein]
    for dat in ["p", "p_last", "fp_existing", "fp_future", "claim"]:
        pvt = data.pivot_table(
            "rein_" + dat, "complete_lob", div_field, aggfunc="sum"
        ).fillna(0)
        prem_res[(rein, dat)] = prem_res[("calc net", dat)].add(
            pvt, fill_value=0
        )

std_dev = sam_scr.f_data("data", "metadata", "std_dev_prem_res").loc[
    lob["lob"]
]

end=time.perf_counter()
elapsed = end - start
print(f'Time taken Step {n}: {elapsed:.6f} seconds')

start=time.perf_counter()
n+=1


######


#import numpy as np

# add_values = ["gross", "net", "calc net", "reinsurance"]
# for val in [*calc_list, *add_values]:
#     for dat in ["p", "p_last", "fp_existing", "fp_future", "claim"]:
#         cols = prem_res[(val, dat)].columns
#         prem_alloc[(val, dat)] = prem_res[(val, dat)].values @ df_allocation[cols].T.values

#     p = prem_alloc[(val, "p")]
#     p_last = prem_alloc[(val, "p_last")]
#     prem_alloc[(val, "premium")] = np.where(p > p_last, p, p)
#     prem_alloc[(val, "premium")] += prem_alloc[(val, "fp_existing")] + prem_alloc[(val, "fp_future")]

#     sigma = {}
#     sigma["premium"] = np.einsum("ij,il->il", std_dev[["prem"]], prem_alloc[(val, "premium")])
#     sigma["reserve"] = np.einsum("ij,il->il", std_dev[["res"]], prem_alloc[(val, "claim")])
#     sigma["overall"] = np.sqrt(
#         np.square(sigma["premium"])
#         + 2 * 0.5 * sigma["premium"] * sigma["reserve"]
#         + np.square(sigma["reserve"])
#     )

#     temp = {}
#     for calc in ["premium", "reserve", "overall"]:
#         temp[calc] = np.sqrt(
#             np.einsum("ij,jk,ki->i", sigma[calc].T, corr.values, sigma[calc])
#         )
#         output[val] = pd.DataFrame(temp)
#         output[val].index = df_allocation.index







#######

# add_values = ["gross", "net", "calc net", "reinsurance"]
# for val in [*calc_list, *add_values]:
#     for dat in ["p", "p_last", "fp_existing", "fp_future", "claim"]:
#         cols = prem_res[(val, dat)].columns
#         prem_alloc[(val, dat)] = prem_res[(val, dat)].dot(df_allocation[cols].T)

#     p = prem_alloc[(val, "p")]
#     p_last = prem_alloc[(val, "p_last")]
#     prem_alloc[(val, "premium")] = p.where(p > p_last, p).fillna(p)
#     prem_alloc[(val, "premium")] = (
#         prem_alloc[(val, "premium")]
#         + prem_alloc[(val, "fp_existing")]
#         + prem_alloc[(val, "fp_future")]
#     )

#     sigma = {}
#     sigma["premium"] = np.einsum(
#         "ij,il->il", std_dev[["prem"]], prem_alloc[(val, "premium")]
#     )
#     sigma["reserve"] = np.einsum(
#         "ij,il->il", std_dev[["res"]], prem_alloc[(val, "claim")]
#     )
#     sigma["overall"] = np.sqrt(
#         np.square(sigma["premium"])
#         + 2 * 0.5 * sigma["premium"] * sigma["reserve"]
#         + np.square(sigma["reserve"])
#     )

#     temp = {}
#     for calc in ["premium", "reserve", "overall"]:
#         temp[calc] = np.sqrt(
#             np.einsum("ij,jk,ki->i", sigma[calc].T, corr, sigma[calc])
#         )
#         output[val] = pd.DataFrame(temp)
#         output[val].index = df_allocation.index

# end=time.perf_counter()
# elapsed = end - start
# print(f'Time taken Step {n}: {elapsed:.6f} seconds')

# start=time.perf_counter()
# n+=1

# # We now need to merge the various dataframes for the different
# # couterparties into single dataframes
# dic_reinsurance = [
#     df.assign(counterparty=party)
#     for party, df in output.items()
#     if party not in add_values
# ]
# df_reinsurance = pd.concat(dic_reinsurance)
# df_net = output["calc net"]
# df_default = pd.merge(
#     df_net, df_reinsurance, left_index=True, right_index=True, how="left"
# )
# for calc in ["premium", "reserve", "overall"]:
#     df_default[calc] = df_default[calc + "_y"] - df_default[calc + "_x"]
# df_default = df_default[["counterparty", "premium", "reserve", "overall"]]
# output["default"] = df_default


# end=time.perf_counter()
# elapsed = end - start
# print(f'Time taken Step {n}: {elapsed:.6f} seconds')

    #logger.debug("Function start")
    # Get the different combinations of products
    diversification = sam_scr.output["list_combinations"]
    # These are all the columns that will be included in our result.
    res_columns = ["premium", "reserve", "premium_reserve", "lapse_risk"]

    nat_cat_headings = [
        "hail",
        "earthquake",
        "horizontal_1",
        "horizontal_2",
        "horizontal_3",
        "horizontal_4",
        "horizontal_total",
    ]

    other_cat = [
        "nat_cat",
        "mm_motor",
        "mm_fire_property",
        "mm_marine",
        "mm_aviation",
        "mm_liability",
        "mm_credit_guarantee",
        "mm_terrorism",
        "mm_accident_health",
        "man_made",
        "np_property",
        "np_credit_guarantee",
        "non_prop",
        "catastrophe_1",
        "catastrophe_2",
        "catastrophe",
    ]

    factor_perils = sam_scr.f_data("factor_cat", "events")["peril"].values

    other_risk_columns = ["stop_loss", "other", "adj_loss", "non_life", "lapse"]

    market_columns = sam_scr.f_data("market_risk", "market_shocks", "None")
    market_columns = market_columns["columns"].values.tolist()

    total_columns = [
        "market",
        "bscr",
        "op_risk_prem",
        "op_risk_reserve",
        "operational_risk",
        "participations",
        "lacdt",
        "scr",
    ]

    res_columns = [
        *res_columns,
        *factor_perils,
        *nat_cat_headings,
        *other_cat,
        *other_risk_columns,
        *market_columns,
        *total_columns,
    ]

    # We store both the gross and the next results
    # We will use various loops to aggregate the variosu charges
    results = {}

    # Blanks dataframes are created, populated with the value of 0.
    # Avoids any issues with 'na' figures.

    # Most of the impairment charges will be added last
    # Need to make sure that we have a float array to prevetn errors
    for res in ["gross", "net", "impairment", "gross_return"]:
        results[res] = pd.DataFrame(
            0.0, index=diversification["combinations"], columns=res_columns
        )

    # PREMIUM AND RESERVE RISK

    for chrg in ["gross", "net"]:
        if chrg == "net":
            mod_chrg = "calc net"
        else:
            mod_chrg = chrg
        hf.f_best_join(
            left_df=results[chrg],
            right_df=sam_scr.f_data("prem_res", mod_chrg, "all"),
            dest_field=["premium", "reserve", "premium_reserve"],
            source_field=["premium", "reserve", "overall"],
        )

    # Populate that the gross figures
    results["gross_return"][["premium", "reserve", "premium_reserve"]] = results[
        "gross"
    ][["premium", "reserve", "premium_reserve"]]

    # LAPSE RISK

    div_level = sam_scr.f_data("data", "data", "diversification_level").iloc[0]
    lapse_data = sam_scr.f_data("data", "data", "division_detail")[
        [div_level, "lapse_risk"]
    ].fillna(0)
    hf.f_accummulate_figures(
        dest_df=results["gross"],
        source_df=lapse_data,
        dest_col="lapse_risk",
        source_col="lapse_risk",
        dest_index=True,
        source_index=False,
        source_index_col=div_level,
        agg_func="sum",
    )

    # Copy the lapse risk across to the other dataframes
    results["net"]["lapse_risk"] = results["gross"]["lapse_risk"]
    results["impairment"]["lapse_risk"] = results["gross"]["lapse_risk"]
    results["gross_return"]["lapse_risk"] = results["gross"]["lapse_risk"]

    # Now we populate the natural catastrophe risk charges
    hf.f_best_join(
        left_df=results["gross"],
        right_df=sam_scr.f_data("nat_cat", "base", "all"),
        dest_field=nat_cat_headings,
        source_field=nat_cat_headings,
    )

    # FACTOR BASED CATASTROPHE RISK

    factor_perils = sam_scr.f_data("factor_cat", "events")["peril"].values.tolist()
    # We need to populate the factor cat charges
    # We don't have aligned with our factor charges
    hf.f_best_join(
        left_df=results["gross"],
        right_df=sam_scr.f_data("factor_cat", "base", "all"),
        dest_field=factor_perils,
        source_field=factor_perils,
    )

    # MAN-MADE CATASTROPHE RISK
    # The man made perils
    mm_perils = [
        "mm_motor",
        "mm_fire_property",
        "mm_marine",
        "mm_aviation",
        "mm_liability",
        "mm_credit_guarantee",
        "mm_terrorism",
        "mm_accident_health",
    ]
    hf.f_best_join(
        left_df=results["gross"],
        right_df=sam_scr.f_data("man_made_cat", "man_made_cat", "all"),
        dest_field=mm_perils,
        source_field=mm_perils,
    )

    # NON-PROPORTIONAL CATASTROPHE RISK
    # The non-prop based perils
    np_perils = ["np_property", "np_credit_guarantee"]
    hf.f_best_join(
        left_df=results["gross"],
        right_df=sam_scr.f_data("non_prop_cat", "base", "np_all"),
        dest_field=np_perils,
        source_field=np_perils,
    )

    # POPULATE REINSURANCE FIGURES

    # NEED TO POPULATE IMPAIRMENT FIGURES

    # For the impairment we need to add our charges
    # For this we will get all of the data in a single dataframe
    right_df = sam_scr.f_data("market_risk", "impairment_charge", "all")
    #print("aggregation " + type(right_df).__name__)
    hf.f_best_join(
        left_df=results[chrg],
        right_df=right_df,
        dest_field=[
            *["premium_reserve", "hail", "earthquake", "horizontal_total"],
            *factor_perils,
            *mm_perils,
            *np_perils,
        ],
        source_field=[
            *["prem_res", "hail", "earthquake", "horizontal"],
            *factor_perils,
            *mm_perils,
            *np_perils,
        ],
    )

    # AGGREGATION OF THE DIFFERENT EVENTS

    # TODO:
    # Need to add the man made charges to the calculation
    # Aggregate the nat cat charges
    # Need to worry how it is dislcosed when the net event can win here.
    # This is the primary purpose of the resuslts

    # AGGREGATE THE CATASTROPHE RISK CHARGES

    for chrg in ["gross", "net", "impairment", "gross_return"]:
        # Natural Catastrophe calculation
        results[chrg]["nat_cat"] = results[chrg][
            ["hail", "earthquake", "horizontal_total"]
        ].max(axis=1)

        # Factor based cacculation
        results[chrg]["catastrophe_2"] = np.square(results[chrg][factor_perils]).sum(
            axis=1
        ) + np.square(
            results[chrg][["fc_accident_health", "fc_non_prop_accident_health"]]
        ).sum(
            axis=1
        )

        results[chrg]["catastrophe_2"] = np.sqrt(results[chrg]["catastrophe_2"])
        # Man made peril calculation
        results[chrg]["man_made"] = np.sqrt(
            np.square(results[chrg][mm_perils]).sum(axis=1)
        )
        # Non-prop calculation.
        results[chrg]["non_prop"] = np.sqrt(
            np.square(results[chrg][np_perils]).sum(axis=1)
        )

        # Calcualte for catastrophe 1 cahrges
        results[chrg]["catastrophe_1"] = np.sqrt(
            np.square(results[chrg][["nat_cat", "man_made", "non_prop"]]).sum(axis=1)
        )

        # Aggregate the overall catastrophe charges
        results[chrg]["catastrophe"] = np.sqrt(
            np.square(results[chrg][["catastrophe_1", "catastrophe_2"]]).sum(axis=1)
        )

    # REPORTED RESULTS

    # For the reported results we need to take the maximum of the
    # net perils after allowance for impairment.

    # AGGREGATE THE NON-LIFE RISK CHARGES

    # We don't need matrix multiplication as the 3 x 3 matrix simplifies.
    # This is done to avoid the use of eigen sums
    for chrg in ["gross", "net", "impairment"]:
        results[chrg]["non_life"] = np.sqrt(
            results[chrg]["premium_reserve"] ** 2
            + 2 * 0.25 * results[chrg]["premium_reserve"] * results[chrg]["catastrophe"]
            + results[chrg]["catastrophe"] ** 2
            + results[chrg]["lapse"] ** 2
        ) + (results[chrg][["stop_loss", "other", "adj_loss"]].sum(axis=1))

    # MARKET RISK CHARGES

    # The market risk values are stored in a seeprate dataframe.
    # We won't bring in all the market risk shocks.
    # these will be output seeprately.
    # We only get the total market risk at this stage.

    hf.f_best_join(
        results["gross"],
        sam_scr.f_data("market_risk", "summary_data"),
        market_columns,
        market_columns,
    )
    # Copy the gross market risk results into the net data.
    results["net"].loc[:, "market"] = results["gross"]["market"]

    # AGGREGATE THE BSCR FIGURES

    # Haven't made allowance (now) for life risk
    for chrg in ["gross", "net"]:
        results[chrg]["bscr"] = np.sqrt(
            results[chrg]["non_life"] ** 2
            + 2 * 0.25 * results[chrg]["non_life"] * results[chrg]["market"]
            + results[chrg]["market"] ** 2
        )

    # OPERATIONAL RISK

    # We add operational risk to our calculation
    for chrg in ["gross", "net"]:
        results[chrg]["operational_risk"] = results[chrg][
            ["op_risk_prem", "op_risk_reserve"]
        ].max(axis=1)
        # Apply the 30% cap to the calcaultion
        results[chrg]["operational_risk"].where(
            results[chrg]["operational_risk"] <= 0.3 * results[chrg]["bscr"],
            other=0.3 * results[chrg]["bscr"],
            inplace=True,
        )

    # LACDT CALCULATION

    # Now we need to add the LACDT calcaultion.
    # It does need to base SCR figure
    base_scr = {}
    for res in ["gross", "net", "impairment", "gross_return"]:
        tmp = results["gross"][["bscr", "operational_risk", "participations"]].sum(
            axis=1
        )
        tmp.name = res
        base_scr[res] = tmp

    tax_calc = f_lacdt_calculation(sam_scr, base_scr)

    # SCR CALCULATION

    # We first need to create a blank entry
    # res = {}
    # sam_scr.output[calc_name]={}
    for chrg in ["gross", "net", "impairment", "gross_return"]:
        results[chrg].loc[results[chrg].index, "lacdt"] = (
            -1 * tax_calc.loc[results["gross"].index, chrg + "_lacdt"]
        )
        results[chrg]["scr"] = (
            results[chrg]["bscr"]
            + results[chrg]["operational_risk"]
            + results[chrg]["participations"]
            + results[chrg]["lacdt"]
        )