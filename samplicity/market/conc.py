"""
conc.

A module containing the calculation of concentration risk.
This supports the Market class

@author: chogarth


"""
import pandas as pd
import math
from numpy import nan_to_num, unique, sqrt
from ..helper import log_decorator

#logger = logging.getLogger(__name__)

#@log_decorator
def f_concentration_risk(mr):
    """Calculate concentration risk."""
    #logger.debug("Function start")
    # Concentration risk has similarities to credit (type 1) default risk.
    # However a big difference is that we do not need to re-produce the
    # calculation for reinsurance

    # In calcualting the concentration risk we need to allocate collateral
    # to all of the assets.
    # We identify the assets based on the 'conc_ind' field
    # We don't use the market value as market values could be
    # zero, negative or positive
    # An indidicator is more accurate

    # We are going to copy the data into a seperate data frame.
    # Effectively it doesn't make sense to add all of the additional
    # fields to the main market risk table
    # The data frame gets too wide
    # For now we will store the variable and then destroy it.
    # For audit trial purposes this could be cahnged.

    # We use '>1" as we differentiate between
    # - 1 Government aseets
    # - 2 Bank deposits
    # - 3 Normal (other) assets
    incl_assets = mr.output["asset_data"]["conc_ind"] >= 1

    # Need to make allowance for the rare instance where there
    # could be no concentration riks
    if incl_assets.sum() == 0:
        return pd.DataFrame(
            0.0, index=mr.output["df_allocation"].index, columns=["result"]
        )

    # At this stage we know we have valid data

    # We differentiate betwwen 3 types of counterparties:
    # - 1 Government: Inlcuded but doesn't get shocks
    # - 2 Normal: Inlcuded and shocked normally
    # - 3 Bank: SHocked at lower rates and treated as separate to
    #           other counterparties

    # Create a deep copy of our data.
    # Only copying the fields we actually need.
    conc_data = mr.output["asset_data"].loc[incl_assets, :].copy(deep=True)
    conc_data = conc_data[
        [
            "conc_cqs",
            "market_value",
            "collateral",
            "lgd",
            "id",
            "counterparty_group",
            "counterparty_id",
            "conc_type",
            "conc_ind",
            mr.output["div_field"],
        ]
    ]
    # include_default=conc_data[conc_data.conc_type!='government']

    conc_data["add_collateral"] = 0.0

    conc_data["mv_net_colateral"] = conc_data["market_value"].fillna(0) - conc_data[
        "collateral"
    ].fillna(0)
    conc_data["mv_net_colateral"].where(
        conc_data["mv_net_colateral"] > 0, other=0, inplace=True
    )

    # These calculations are repeated from Type 1 credit risk.
    # However, the calcualtion is

    cparty_totals = conc_data[["mv_net_colateral", "counterparty_id"]]
    cparty_totals = cparty_totals.groupby(by="counterparty_id", as_index=True).sum()

    # We do it this way around because alsmsot always there will be no
    # collateral. We save a join inthe program
    cparty_collat = mr.output["counterparty"]
    cparty_collat = cparty_collat.loc[
        cparty_collat["counterparty_collateral"] > 0, "id"
    ]

    if len(cparty_collat) > 0:
        for co in cparty_collat.id:
            collateral = mr.output["counterparty"].at[co, "cparty_collateral"]
            incl_cparty = conc_data["conterparty_id"] == co
            # Need to allow for the case that there are no counterparties
            if sum(incl_cparty) > 0:
                mv_net_colateral = cparty_totals.at[co, "mv_net_colateral"]
                conc_data.loc[incl_cparty, "add_collateral"] = collateral * (
                    conc_data.loc[incl_cparty, "mv_net_collateral"] / mv_net_colateral
                )

    conc_data["lgd_calc"] = conc_data["lgd"] * (
        conc_data["market_value"]
        - conc_data["collateral"]
        - conc_data["add_collateral"]
    )
    conc_data["lgd_cqs_calc"] = (
        conc_data["conc_cqs"]
        * conc_data["lgd"]
        * (
            conc_data["market_value"]
            - conc_data["collateral"]
            - conc_data["add_collateral"]
        )
    )

    # we apply this calcualtion to only include assets with a default
    # in the CQS calculation.
    conc_data["lgd_calc_mod"] = conc_data["lgd_calc"].where(
        conc_data["lgd_calc"] > 0, other=0
    )
    conc_data["lgd_cqs_calc_mod"] = conc_data["lgd_cqs_calc"].where(
        conc_data["lgd_calc"] > 0, other=0
    )

    # Now we have an issue
    # We need to treat banks and other counterparties differently
    # Want to gorup government together to reduce the number of
    # calculation columns
    conc_data["counterparty_group_type"] = (
        str(conc_data["counterparty_group"]) + "__" + conc_data["conc_type"] + "__"
    )
    conc_data.loc[
        (conc_data["conc_type"] == "government"), "counterparty_group_type"
    ] = "__government__"

    conc_calc = {}
    for fld in [
        "lgd_calc",
        "lgd_cqs_calc",
        "lgd_calc_mod",
        "lgd_cqs_calc_mod",
        "market_value",
    ]:
        conc_calc[fld] = conc_data.pivot_table(
            fld, mr.output["div_field"], "counterparty_group_type", aggfunc="sum"
        )
        conc_calc[fld] = mr.output["df_allocation"][conc_calc[fld].index].dot(
            conc_calc[fld]
        )

    # We need the asset sums by total, don't need for eahc counterparty
    # Haven't allowed to reduce concentration risk for any potential
    # negative asset value
    conc_calc["market_value"] = conc_calc["market_value"].sum(axis=1)

    # We now remove the neagtive exposure vlaues for counterparties
    conc_calc["lgd_calc"].where(conc_calc["lgd_calc"] > 0, other=0, inplace=True)

    # We calcualte the weighted CQS where our exposure is positive
    conc_calc["cqs"] = conc_calc["lgd_cqs_calc_mod"] / conc_calc["lgd_calc_mod"]
    conc_calc["cqs"] = conc_calc["cqs"].fillna(19)
    conc_calc["cqs"] = conc_calc["cqs"].applymap(
        lambda x: math.floor(min(19, max(1, nan_to_num(x, nan=18))))
    )

    # We perform a seperate calculation for bank and other
    conc_calc["excess"] = pd.DataFrame(
        0.0, columns=conc_calc["lgd_calc"].columns, index=conc_calc["lgd_calc"].index
    )

    cqs_unique = unique(conc_calc["cqs"])

    for cqs in cqs_unique:
        for calc in ["bank", "other"]:
            calc_col = "__" + calc + "__"
            include_cols = [
                string.endswith(calc_col) for string in conc_calc["excess"].columns
            ]
            include = pd.DataFrame(
                False,
                columns=conc_calc["lgd_calc"].columns,
                index=conc_calc["lgd_calc"].index,
            )
            include[(conc_calc["cqs"].loc[:, include_cols] == cqs)] = True
            excess = (
                mr.data_meta["conc_factors"].loc[cqs, "ct_" + calc]
                * conc_calc["market_value"]
            )
            g = mr.data_meta["conc_factors"].loc[cqs, "g"]
            # My need to broadcast dimentions here
            # m-v[:, None]
            conc_calc["excess"][include] = conc_calc["lgd_calc"][include] - excess
            conc_calc["excess"][include] = conc_calc["excess"][include] * g
            conc_calc["excess"][include].where(
                conc_calc["excess"][include] > 0, other=0, inplace=True
            )

    # We now need to map our data in cqs
    # It is currently by counterparty

    conc_calc["conc"] = conc_calc["excess"].pow(2).sum(axis=1)
    conc_calc["conc"] = sqrt(conc_calc["conc"])

    # We store the result as part of the market risk class
    return pd.DataFrame(
        conc_calc["conc"], index=mr.output["df_allocation"].index, columns=["result"]
    )
