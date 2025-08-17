"""
credit.

A module containing the calculation of type 1 credit risk.
This supports the Market class

@author: chogarth


"""
from __future__ import annotations
from typing import TYPE_CHECKING
import pandas as pd
import numpy as np
import itertools
from typing import Dict, Tuple
if TYPE_CHECKING:
    from .. import MarketRisk


from ..helper import f_get_total_row, f_new_match_idx, combins_df_col


def calculate_u_matrix_entry(p: Tuple[float, float]) -> float:
    """Calculate an individual entry for the U matrix."""
    gam = 0.25
    num = p[0] * (1 - p[0]) * p[1] * (1 - p[1])
    denom = (1 + gam) * (p[0] + p[1]) - p[0] * p[1]
    return num / denom


def f_u_matrix(mr: MarketRisk) -> np.ndarray:
    """Calculate the U matrix used in Type 1 credit risk."""
    cf = mr.scr.f_data("data", "metadata", "credit_type_1_factor")
    factors = cf["factor"]

    u_matrix = np.array(
        [calculate_u_matrix_entry(p) for p in itertools.product(factors, repeat=2)]
    )
    return u_matrix.reshape(len(factors), len(factors))


def f_v_vector(mr: MarketRisk) -> np.ndarray:
    """Generate the V vector used in Type 1 credit risk calculations."""
    gam = 0.25
    cf = mr.scr.f_data("data", "metadata", "credit_type_1_factor")
    return np.array(
        ((1 + 2 * gam) * cf["factor"] * (1 - cf["factor"]))
        / (2 + 2 * gam - cf["factor"])
    )


def f_impairment(mr: MarketRisk) -> Dict[str, pd.DataFrame]:
    """Calculate the impairment charges for the reinsurance across all the relevant events."""

    # This gets populated with the names of all the different events
    impair = {}

    # Premium Reserve Risk

    # If we have no reinsurance, there will be no default cashflows
    # and data will be None
    data = mr.scr.f_data("prem_res", "default", "all")
    if data is not None:
        # Only need the overall figures
        # We rename the columns to comply with the function
        data = data.rename(
            columns={"overall": "reinsurance_mv", "counterparty": "counterparty_id"}
        ).drop(columns=["premium", "reserve"])
        # The dataset will return figures for all diversification combinations.
        # We only want the data for the entries all the combinations
        total = f_get_total_row(data).set_index("counterparty_id")
        impair["prem_res"] = __f_default(mr, ri_exposure=data, total_exposure=total)
    else:
        # Deals witht he case when there is no reinsurance on premium and reserve risk
        impair["prem_res"] = None

    # Catastrophe Events

    # Create a list and look through all the events at once
    events = [
        *["nc_hail", "nc_earthquake", "nc_horizontal"],
        *mr.scr.f_data("data", "metadata", "factor_cat_charge").index,
        *["np_property", "np_credit_guarantee"],
    ]

    for event in events:
        # Get the recovery at an individual counterparty level
        # This wil return a dataframe with the counterparty id, the recoveries
        data = mr.scr.f_data("reinsurance", "counterparty_recoveries", event)
        if data is not None:
            data = data.rename(columns={"recovery": "reinsurance_mv"})
            # Get the total recoveries for the event
            total = mr.scr.f_data("reinsurance", "recoveries", event).rename(
                columns={"cparty_recov": "reinsurance_mv"}
            )
            impair[event] = __f_default(mr, ri_exposure=data, total_exposure=total)
        else:
            # Deals with the case when there is no reinsurance on the event
            impair[event] = None

    return impair


def f_credit_type_1(mr: MarketRisk) -> pd.DataFrame:
    """Type 1 credit risk calculation."""
    # We use the same calcualtion to determine reinsurer impairment
    # In the case of credit risk these figures will be None and can be ignored
    return __f_default(mr, ri_exposure=None, total_exposure=None)


def __f_default(mr: MarketRisk, ri_exposure, total_exposure) -> pd.DataFrame:
    """Calculate Type 1 Credit Risk."""
    # This is not a straight forward calculation
    # It is also not clear if the calcualtion should be done per
    # countertary or at a group level. Particularly as the calcualtion
    # calls for independent counterparties, which suggests a group level.
    # The allocation of collateral becomes an issue as it impacts the
    # weighting for the counterparty default impairment

    """
    We have a couple challenges with the collateral and how we 
    should treat it for reinsurance recoveries. Effectivley we allocate 
    collateral at an overall level but then we allocate the assets to 
    the different products, divisions,etc. We will allocate the 
    reinsurance recoveries for the entire license and then that will 
    determine the allocation of collateral to the different assets
    """

    # Retrieve the asset credit data and counterparty information
    # Perform some data manipulation to prepare the data for the calculation
    # credit_data has the different assets
    # cparty_collat has the counterparties with collateral
    credit_data, cparty_collat = __f_data_manip(mr)

    if total_exposure is not None:
        # A double chekc to make sure that we don't include negative values.
        # Can't imagine this happening.
        total_exposure["reinsurance_mv"] = total_exposure["reinsurance_mv"].where(
            total_exposure["reinsurance_mv"] > 0, other=0
        )

    if ri_exposure is not None:
        # Our reinsurance information doesn't have all the required fields.
        # We need to add CQS and LGD fields which come form our market risk
        ri_exposure = __f_ri_data_manip(mr, ri_exposure)

        # Now we allocate the collateral between assets and reinsurance
        # We then allocate capital to the different assets.

        credit_data, ri_exposure = __f_alloc_collat(
            credit_data, ri_exposure, total_exposure, cparty_collat
        )

    # We now need to calculate the weighted CQS for the combinations of assets
    # We can't combine the reinsurance and assets at this stage as
    # the allocation is not linear

    asset_data = __f_calc_cqs(mr, credit_data)

    # We know allocate the assets to all the different combinations
    # We need to pivot each dataset, this is handled here
    asset_calc = __f_pivot_asset(mr, asset_data, rein=False)

    if ri_exposure is not None:
        # TODO: Need to edit the data manipulation to ensure field consistency
        ri_calc = __f_calc_cqs(mr, ri_exposure)

        # We also need to pivot the RI data here
        ri_calc = __f_pivot_asset(mr, ri_calc, rein=True)

        # We don't need to do the same alloation as with the asset data
        # This has already been done for the reinsurance data
        # We still need to join them.
        # We need every combination of asset and reinsurance data

        asset_calc = __f_join_data(mr, asset_calc, ri_calc)

    # We have our combined datasets we can now perform the calculation

    overall_result = __f_credit_calc(mr, asset_calc)
    overall_result.fillna(0, inplace=True)

    # We now need to decdie if we return the base calcualtion or
    # subtract type 1 credit risk. We only subtract type 1 credit risk if
    # this is an impairment calculation

    if ri_exposure is not None:
        # We are dealing with an impairment charge
        credit_charge = mr.output["credit_type_1_charge"]

        match = f_new_match_idx(
            overall_result.index.to_series(), credit_charge.index.to_series()
        )
        match = match.to_frame(name="div")
        credit_charge = match.merge(
            credit_charge, how="left", left_on="div", right_index=True
        )

        overall_result = overall_result - credit_charge["result"]
        # overall_result=overall_result.to_frame(name='result')
    # We store the result as part of the market risk class
    return pd.DataFrame(overall_result.to_frame(name="result"))


def __f_data_manip(mr: MarketRisk) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform required data manipulation on the asset credit data.

    This involves extracting the credit data from the base market data and performing
    all of the necessary calculations to calculate the net exposure. The function filters
    for credit instruments, calculates market value net of collateral, and extracts
    counterparty collateral information.

    :param mr: Market risk object containing output data including asset_data and counterparty information
    :type mr: MarketRisk

    :returns: Tuple containing processed credit data:

        - **credit_data** (*pandas.DataFrame*) -- Filtered and processed credit asset data with columns:
            - 'id': Asset identifier
            - 'market_value': Market value of the asset
            - 'collateral': Collateral amount captured directly against the asset
            - 'lgd': Loss given default parameter
            - 'used_cqs': Credit quality step used
            - 'counterparty_group': Counterparty group identifier
            - 'counterparty_id': Individual counterparty identifier
            - mr.output["div_field"]: Diversification field (dynamic column name)
            - 'mv_net_collateral': Calculated market value net of collateral (non-negative)
            - 'add_collateral': Additional collateral field (initialized to 0)
            - 'lgd_calc': LGD calculation field (initialized to 0)
            - 'lgd_cqs_calc': LGD CQS calculation field (initialized to 0)
        - **cparty_collat** (*pandas.DataFrame*) -- Counterparty collateral data containing only counterparties with positive collateral amounts

    :rtype: tuple[pandas.DataFrame, pandas.DataFrame]

    .. note::
        - Only assets with credit_type_1_ind > 0 are included in the output
        - Negative net exposures are set to zero to remove negative exposures
        - Missing values in market_value and collateral are treated as zero

    .. warning::
        This is an internal function and should not be called directly by users. Instead users chould call 'f_credit_type_1'
    """

    # MANIPULATE ASSET CREDIT DATA

    credit_data = mr.output["asset_data"].copy(deep=True)
    # counterparty=mr.output['counterparty']
    credit_data = credit_data.loc[credit_data["credit_type_1_ind"] > 0, :]
    credit_data = credit_data[
        [
            "id",
            "market_value",
            "collateral",
            "lgd",
            "used_cqs",
            "counterparty_group",
            "counterparty_id",
            mr.output["div_field"],
        ]
    ]

    credit_data[["mv_net_collateral", "add_collateral", "lgd_calc", "lgd_cqs_calc"]] = 0

    credit_data["mv_net_collateral"] = credit_data["market_value"].fillna(
        0
    ) - credit_data["collateral"].fillna(0)

    # Make sure we remove the negative exposures.
    credit_data["mv_net_collateral"] = credit_data["mv_net_collateral"].where(
        credit_data["mv_net_collateral"] > 0, other=0
    )

    # GET COLLATERAL INFORMATION

    cparty_collat = mr.output["counterparty"].copy(deep=True)
    cparty_collat = cparty_collat.reindex(cparty_collat["id"])
    cparty_collat = cparty_collat.loc[
        cparty_collat["counterparty_collateral"] > 0, ["counterparty_collateral"]
    ]

    return (credit_data, cparty_collat)


def __f_ri_data_manip(mr: MarketRisk, ri_exposure):
    """Manipulate the reinsurance data."""

    # We now need to add the CQS and LGD fields to the data
    # We get that from the counterparty table
    counterparty = mr.output["counterparty"].copy(deep=True)
    ri_exposure.reset_index(inplace=True)
    ri_exposure = ri_exposure.merge(
        counterparty[["counterparty_group", "counterparty_cqs", "id"]],
        how="left",
        left_on="counterparty_id",
        right_on="id",
    )
    ri_exposure.rename(
        columns={"counterparty_cqs": "used_cqs", "reinsurance_mv": "market_value"},
        inplace=True,
    )
    ri_exposure[["collateral", "add_collateral"]] = 0
    ri_exposure = ri_exposure[
        [
            "index",
            "counterparty_id",
            "counterparty_group",
            "market_value",
            "collateral",
            "add_collateral",
            "used_cqs",
        ]
    ]

    # We make sure that any missign cqs if populated with 18
    # Really shouldn't happen if we have all counterparties populated
    if ri_exposure["used_cqs"].isna().sum() > 0:
        # mr.scr.handle_warning(
        #     "__f_ri_data_manip",
        #     "Missing CQS values in reinsurance data",
        #     f"{ri_exposure['used_cqs'].isna().sum()}",
        # )
        ri_exposure["used_cqs"] = ri_exposure["used_cqs"].fillna(18)

    if ri_exposure["counterparty_group"].isna().sum() > 0:
        # mr.scr.handle_warning(
        #     "__f_ri_data_manip",
        #     "Missing counterparty group names in reinsurance data",
        #     f"{ri_exposure['counterparty_group'].isna().sum()} values converted",
        # )
        ri_exposure["counterparty_group"] = ri_exposure["counterparty_group"].fillna(
            ri_exposure["counterparty_id"]
        )

    ri_exposure["lgd"] = 0.45

    return ri_exposure


def __f_alloc_collat(credit_data, ri_exposure, total_exposure, cparty_collat):
    """Allocate collateral to the different assets."""

    # AGGREGATE CREDIT ASSET DATA

    cparty_totals = credit_data[["mv_net_collateral", "counterparty_id"]]
    cparty_totals = cparty_totals.groupby(by="counterparty_id", as_index=True).sum()
    cparty_totals.rename(columns={"mv_net_collateral": "asset_mv"}, inplace=True)

    # We now merge our collaterla data onto our credit and reinsurer data.
    collat_alloc = cparty_collat.merge(
        cparty_totals, how="outer", left_index=True, right_index=True
    )
    if total_exposure is not None:
        collat_alloc = collat_alloc.merge(
            total_exposure["reinsurance_mv"],
            how="outer",
            left_index=True,
            right_index=True,
        )
    else:
        # We need a blank calculation for the generic case.
        collat_alloc["reinsurance_mv"] = 0

    # Set any blank vlaues to be zero.
    collat_alloc = collat_alloc.astype(float)
    collat_alloc.fillna(0, inplace=True)

    # We now calcualte the collateral allocation split between
    # the reinsurance and market data.
    # We need to use this when we do the division based calculations
    # For the overall view it won't matter.
    collat_alloc["total_mv"] = collat_alloc[["asset_mv", "reinsurance_mv"]].sum(axis=1)

    perc_share = collat_alloc[["asset_mv", "reinsurance_mv"]].divide(
        collat_alloc["total_mv"], axis="rows"
    )
    collat_alloc[["asset_collat", "reinsurance_collat"]] = perc_share.mul(
        collat_alloc["counterparty_collateral"], axis="rows"
    ).values
    # The above will create division by zero, we we remove these
    # Allow division by zero 'error' to shorten code
    collat_alloc.fillna(0, inplace=True)

    # At this stage we know the collateral that must be allocted to
    # the assets and the reinsurance recoveries

    # ALLOCATE TO THE ASSET DATA

    # We now need to allocate the collateral to the counterparties
    # in the asset data
    # Get the prcentage of the toal MV
    credit_data["add_collateral"] = credit_data["mv_net_collateral"].divide(
        cparty_totals.loc[credit_data["counterparty_id"], "asset_mv"].values
    )
    # Allocate te collateral accordingly
    credit_data["add_collateral"] = (
        credit_data["add_collateral"]
        * collat_alloc.loc[credit_data["counterparty_id"], "asset_collat"].values
    )

    # ALLOCATE THE REINSURANCE RECOVERIES

    # In this dataframe we have all of the events allocated to
    # the different divisions
    # The collateral first needs to be prorated.
    # Thsi recognises that teh collateral is onlu a functon of the total
    # agreement. We therefore redcue the collateral proportionately
    # We have an instance where collateral is unique for division

    if (ri_exposure is not None) & (len(cparty_collat) > 0):
        # We also chekc if there is actually any collaterla to allocates
        ri_exposure["add_collateral"] = ri_exposure["reinsurance_mv"].divide(
            collat_alloc.loc[ri_exposure["counterparty_id"], "reinsurance_mv"].values
        )

        # Need to add a minimum in the unlikely event the vlaue is above 1
        # All divisions should be equal to or less than 1
        ri_exposure["add_collateral"] = np.minimum(ri_exposure["add_collateral"], 1)
        # Allocate te collateral accordingly
        ri_exposure["add_collateral"] = (
            ri_exposure["add_collateral"]
            * collat_alloc.loc[
                ri_exposure["counterparty_id"], "reinsurance_collat"
            ].values
        )
    # Deals with the instance where there is no collateral
    elif ri_exposure is not None:
        ri_exposure["add_collateral"] = 0

    return (credit_data, ri_exposure)


def __f_calc_cqs(mr, dat, rein=False):
    """Calcualte CQS for the different combinations of assets."""

    # Calcualte the weigthed average of the LGD based on the exposure
    dat["lgd_calc"] = dat["lgd"] * (
        dat["market_value"] - dat["collateral"] - dat["add_collateral"]
    )
    # We calculated the wieghted average of the CQS based on the losses given default
    dat["lgd_cqs_calc"] = (
        dat["used_cqs"]
        * dat["lgd"]
        * (dat["market_value"] - dat["collateral"] - dat["add_collateral"])
    )

    # we apply this calcualtion to only include assets with a
    # default in the CQS calculation.
    # Settign the field to zero will mean that it won't inlfuence the calculation
    dat["lgd_calc_mod"] = dat["lgd_calc"].where(dat["lgd_calc"] > 0, other=0)
    dat["lgd_cqs_calc_mod"] = dat["lgd_cqs_calc"].where(dat["lgd_calc"] > 0, other=0)

    return dat


def __f_pivot_asset(mr, dat, rein=False):
    """Pivot the asset/reinsurance data with counterparties as rows."""

    calc = {}
    df_alloc = mr.output["df_allocation"]

    if rein:
        idx = "index"
    else:
        idx = mr.output["div_field"]

    for fld in ["lgd_calc", "lgd_cqs_calc", "lgd_calc_mod", "lgd_cqs_calc_mod"]:
        calc[fld] = dat.pivot_table(fld, idx, "counterparty_group", aggfunc="sum")
        calc[fld].fillna(0, inplace=True)
        if not rein:
            calc[fld] = df_alloc[calc[fld].index].dot(calc[fld])

    return calc


def __f_join_data(mr, asset_calc, ri_calc):
    # Generate a matching index between our ri data and the other
    # data, we only want to create this once
    # TODO: Need to work out the error in the join here
    # Possibly don't need this as we can just use df_allocation

    # Teh results are a dictionary
    key = list(asset_calc.keys())[0]

    asset_div = asset_calc[key].index.values
    ri_div = ri_calc[key].index.values

    df_alloc = [*ri_div, *asset_div]
    df_alloc = [item for t in df_alloc for item in t]
    # Get all the unique combinations
    df_alloc = pd.Series(df_alloc).unique()
    df_alloc = pd.DataFrame(df_alloc, columns=["div"])
    calc_level = mr.scr.f_data("data", "data", "calculation_level").iloc[0]
    lst_combins, _ = combins_df_col(df_alloc, "div", calc_level)

    # Merge the asset data
    asset_match = f_new_match_idx(lst_combins, asset_calc[key].index.to_series())
    asset_match = asset_match.to_frame(name="div").reset_index()

    # Add teh reinsurance recoveries
    ri_match = f_new_match_idx(lst_combins, ri_calc[key].index.to_series())
    ri_match = ri_match.to_frame(name="div").reset_index()

    # Loop through the dictionaries
    for k in asset_calc.keys():
        asset_calc[k] = asset_match.merge(
            asset_calc[k], how="inner", left_on="div", right_index=True
        )
        asset_calc[k].drop(columns=["div"], inplace=True)

        ri_calc[k] = ri_match.merge(
            ri_calc[k], how="inner", left_on="div", right_index=True
        )
        ri_calc[k].drop(columns=["div"], inplace=True)

        # New concanenate the daaframes
        # We don't need to wory about getting columns to match
        asset_calc[k] = pd.concat([asset_calc[k], ri_calc[k]], ignore_index=True)

        # We now need a final aggregation to have our data grouped
        asset_calc[k] = asset_calc[k].groupby(by="index", as_index=True).sum()

    return asset_calc


def __f_credit_calc(mr, credit_calc: pd.DataFrame) -> np.ndarray:
    """
    Calculate the credit risk for a given set of credit exposures.

    This function implements the core calculation for Type 1 credit risk under Solvency II.
    It follows these main steps:
    1. Adjust Loss Given Default (LGD) values
    2. Calculate Credit Quality Step (CQS) for each exposure
    3. Aggregate exposures by CQS
    4. Apply correlation factors and risk factors
    5. Calculate the final credit risk charge

    Parameters:
    mr (Market): The Market risk object containing necessary data and parameters
    credit_calc (pd.DataFrame): DataFrame containing credit exposure data
                                Expected columns: lgd_calc, lgd_calc_mod, lgd_cqs_calc_mod

    Returns:
    np.ndarray: Array of credit risk charges for each row in the input DataFrame

    Note: This function assumes that the 'u' and 'v' matrices are pre-calculated
    and stored in mr.output.
    """
    # Adjust LGD values: remove negative exposures and calculate squared LGD
    credit_calc["lgd_calc"] = credit_calc["lgd_calc"].clip(lower=0)
    credit_calc["lgd_calc_2"] = credit_calc["lgd_calc"] ** 2

    # Calculate CQS (Credit Quality Step) for each exposure
    # CQS is bounded between 1 and 18, with 18 as the default for undefined values
    credit_calc["cqs"] = (
        credit_calc["lgd_cqs_calc_mod"] / credit_calc["lgd_calc_mod"]
    ).fillna(18)
    credit_calc["cqs"] = np.floor(credit_calc["cqs"].clip(1, 18)).astype(int)

    # Get unique CQS values and prepare correlation matrices
    cqs_unique = np.unique(credit_calc["cqs"])
    ix_grid = np.ix_(cqs_unique - 1, cqs_unique - 1)
    u = mr.output["u"][ix_grid]  # Correlation matrix
    v = mr.output["v"][cqs_unique - 1]  # Risk factors

    # Prepare DataFrames for sum and sum of squares by CQS
    cqs_columns = [f"cqs_{i}" for i in cqs_unique]
    sum_by_cqs = pd.DataFrame(
        0, index=credit_calc["lgd_calc"].index, columns=cqs_columns
    )
    sum_2_by_cqs = pd.DataFrame(
        0, index=credit_calc["lgd_calc"].index, columns=cqs_columns
    )

    # Aggregate LGD and LGD^2 by CQS
    for cqs in cqs_unique:
        mask = credit_calc["cqs"] == cqs
        sum_by_cqs[f"cqs_{cqs}"] = credit_calc["lgd_calc"][mask].sum(axis=1)
        sum_2_by_cqs[f"cqs_{cqs}"] = credit_calc["lgd_calc_2"][mask].sum(axis=1)

    # Calculate the correlated sum of exposures
    # This represents the systematic risk component
    result_sum = np.einsum("ni,ij,jn->n", sum_by_cqs, u, sum_by_cqs.T)

    # Calculate the sum of squared exposures multiplied by risk factors
    # This represents the idiosyncratic risk component
    result_square = np.einsum("i,hi->h", v, sum_2_by_cqs)

    # Calculate the final credit risk charge
    # The charge is the minimum of:
    # 1. 3 times the square root of (systematic risk + idiosyncratic risk)
    # 2. The sum of all exposures (representing a 100% loss scenario)
    overall_result = np.minimum(
        3 * np.sqrt(result_sum + result_square), sum_by_cqs.sum(axis=1)
    )

    return overall_result
