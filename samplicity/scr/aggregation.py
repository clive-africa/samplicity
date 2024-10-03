# These are the different packages that we require to run our code
import pandas as pd
import numpy as np
from .lacdt import f_lacdt_calculation
from ..helper import log_decorator
from ..import helper as hf


@log_decorator
def _f_agg_scr(sam_scr, calc_name: str = "base_scr", cm: dict = None):
    """Prepare aggregation of the net and gross charges in the SCR.

    Limitations
    -----------
    - The function needs to allow for lapse risk to be populated.
    - The class doesn't allow for life insurance risk
    - diversification calc uses an approximately for the man-made cat.
    - LACDT allowance may be wrong for certain combinations.
      Given the uncertainty, don't believe this is a significant issue.

    Args
    ----
        None

    Returns
    -------
        None:

    """

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
            mod_chrg = "calc_net"
        else:
            mod_chrg = chrg
        hf.f_fast_join(
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
    # This is populated manually
    div_level = sam_scr.f_data("data", "data", "diversification_level").iloc[0]
    lapse_data = sam_scr.f_data("data", "data", "division_detail")[
        [div_level, "lapse_risk"]
    ]
    lapse_data["lapse_risk"]=lapse_data["lapse_risk"].astype(float).fillna(0)

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
    hf.f_fast_join(
        left_df=results["gross"],
        right_df=sam_scr.f_data("nat_cat", "base", "all"),
        dest_field=nat_cat_headings,
        source_field=nat_cat_headings,
    )

    # FACTOR BASED CATASTROPHE RISK

    factor_perils = sam_scr.f_data("factor_cat", "events")["peril"].values.tolist()
    # We need to populate the factor cat charges
    # We don't have aligned with our factor charges
    hf.f_fast_join(
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
    hf.f_fast_join(
        left_df=results["gross"],
        right_df=sam_scr.f_data("man_made_cat", "man_made_cat", "all"),
        dest_field=mm_perils,
        source_field=mm_perils,
    )

    # NON-PROPORTIONAL CATASTROPHE RISK
    # The non-prop based perils
    np_perils = ["np_property", "np_credit_guarantee"]
    hf.f_fast_join(
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
    source_field=[
        *["prem_res", "hail", "earthquake", "horizontal"],
        *factor_perils,
        *mm_perils,
        *np_perils,
    ]


    add_cols =[col for col in source_field if col not in right_df.columns]
    if len(add_cols)>0:
        right_df[add_cols]=0

    #print("aggregation " + type(right_df).__name__)
    hf.f_fast_join(
        left_df=results[chrg],
        right_df=right_df,
        dest_field=[
            *["premium_reserve", "hail", "earthquake", "horizontal_total"],
            *factor_perils,
            *mm_perils,
            *np_perils,
        ],
        source_field=source_field,
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

    hf.f_fast_join(
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
        results[chrg]["operational_risk"]=results[chrg]["operational_risk"].where(
            results[chrg]["operational_risk"] <= 0.3 * results[chrg]["bscr"],
            other=0.3 * results[chrg]["bscr"])

    # LACDT CALCULATION

    # Now we need to add the LACDT calcaultion.
    # It does need to base SCR figure
    base_scr = {}
    for res in ["gross", "net", "impairment", "gross_return"]:
        tmp = results[res][["bscr", "operational_risk", "participations"]].sum(
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
        results[chrg].loc[results[chrg].index, "lacdt"] = tax_calc.loc[results["gross"].index, chrg + "_lacdt"]
        
        results[chrg]["scr"] = (
            results[chrg]["bscr"]
            + results[chrg]["operational_risk"]
            + results[chrg]["participations"]
            + results[chrg]["lacdt"]
        )

        # Save our results to the 'output' frame
        # sam_scr.output[chrg] = results[chrg]
    return results
